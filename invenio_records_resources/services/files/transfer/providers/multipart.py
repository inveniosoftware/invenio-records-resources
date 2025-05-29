# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Multipart file transfer provider."""

from datetime import datetime, timedelta

import marshmallow as ma
from invenio_db.uow import ModelCommitOp
from invenio_files_rest import current_files_rest
from invenio_files_rest.models import FileInstance, ObjectVersion

from ....errors import TransferException
from ....uow import RecordCommitOp, TaskOp
from ...schema import BaseTransferSchema
from ...tasks import (
    recompute_multipart_checksum_task,
)
from ..base import Transfer, TransferStatus
from ..constants import LOCAL_TRANSFER_TYPE, MULTIPART_TRANSFER_TYPE


class MultipartStorageExt:
    """Multipart storage extension.

    If the backend storage supports multipart uploads, this class will delegate
    all calls to the storage backend. Otherwise, it will preallocate the file
    and upload the parts in place using the seek attribute.
    """

    def __init__(self, storage):
        """Constructor."""
        self._storage = storage

    def multipart_initialize_upload(self, parts, size, part_size):
        """
        Initialize a multipart upload.

        :param parts: The number of parts that will be uploaded.
        :param size: The total size of the file.
        :param part_size: The size of each part except the last one.

        :returns: a dictionary of additional metadata that should be stored between
            the initialization and the commit of the upload.
        """
        # if the storage backend is multipart aware, use it
        if hasattr(self._storage, "multipart_initialize_upload"):
            return self._storage.multipart_initialize_upload(parts, size, part_size)

        # otherwise use it as a local storage and pre-allocate the file.
        # In this case, the part size is required as we will be uploading
        # the parts in place to not double the space required.
        if not part_size:
            raise TransferException(
                "Multipart file transfer to local storage requires part_size."
            )
        self._storage.initialize(size=size)
        return {}

    def multipart_set_content(self, part, stream, content_length, **multipart_metadata):
        """
        Set the content of a part.

        This method is called for each part of the
        multipart upload when the upload comes through the Invenio server (for example,
        the upload target is a local filesystem and not S3 or another external service).

        :param part: The part number.
        :param stream: The stream with the part content.
        :param content_length: The content length of the part. Must be equal to the
            part_size for all parts except the last one.
        :param multipart_metadata: The metadata returned by the multipart_initialize_upload
            together with "parts", "part_size" and "size".

        :returns: a dictionary of additional metadata that should be stored as a result of this
            part upload. This metadata will be passed to the commit_upload method.
        """
        if hasattr(self._storage, "multipart_set_content"):
            return self._storage.multipart_set_content(
                part, stream, content_length, **multipart_metadata
            )

        # generic implementation
        part_size = int(multipart_metadata["part_size"])
        parts = int(multipart_metadata["parts"])

        if part > parts:
            raise TransferException(
                "Part number is higher than total parts sent in multipart initialization."
            )

        if part < parts and content_length != part_size:
            raise TransferException(
                "Size of this part must be equal to part_size sent in multipart initialization."
            )

        self._storage.update(
            stream,
            seek=(int(part) - 1) * part_size,
            size=content_length,
        )
        return {}

    def multipart_commit_upload(self, **multipart_metadata):
        """
        Commit the multipart upload.

        :param multipart_metadata: The metadata returned by the multipart_initialize_upload
            and the metadata returned by the multipart_set_content for each part.
        :returns: None or a multipart checksum, if it was computed by the backend.
        """
        if hasattr(self._storage, "multipart_commit_upload"):
            return self._storage.multipart_commit_upload(**multipart_metadata)

    def multipart_abort_upload(self, **multipart_metadata):
        """
        Abort the multipart upload.

        :param multipart_metadata: The metadata returned by the multipart_initialize_upload
            and the metadata returned by the multipart_set_content for each part.
        """
        if hasattr(self._storage, "multipart_abort_upload"):
            return self._storage.multipart_abort_upload(**multipart_metadata)

    def multipart_links(self, base_url, **multipart_metadata):
        """
        Generate links for the parts of the multipart upload.

        :param base_url: The base URL of the file inside the repository.
        :param multipart_metadata: The metadata returned by the multipart_initialize_upload
            and the metadata returned by the multipart_set_content for each part.
        :returns: a dictionary of name of the link to link value
        """
        if hasattr(self._storage, "multipart_links"):
            links = self._storage.multipart_links(**multipart_metadata)
            # TODO: permissions!!! Should not present part links to people that do not have rights to upload
        else:
            links = {}

        if "parts" not in links:
            # generic implementation
            parts = int(multipart_metadata.get("parts", 0))
            if not parts:
                raise TransferException(
                    "Implementation error: Multipart file missing parts tag."
                )
            links["parts"] = [
                {
                    "part": part_no + 1,
                    "url": f"{base_url}/content/{part_no+1}",
                    "expiration": (datetime.utcnow() + timedelta(days=14)).isoformat(),
                }
                for part_no in range(parts)
            ]

        if "content" not in links:
            links["content"] = None

        return links

    def __hasattr__(self, name):
        """Delegate all calls to the storage backend."""
        return hasattr(self._storage, name)

    def __getattr__(self, name):
        """Delegate all calls to the storage backend."""
        return getattr(self._storage, name)


class MultipartTransfer(Transfer):
    """Multipart transfer provider."""

    transfer_type = MULTIPART_TRANSFER_TYPE

    class Schema(BaseTransferSchema):
        """Schema for multipart transfer."""

        part_size = ma.fields.Int(required=False)
        parts = ma.fields.Int(required=True)

    def init_file(self, record, file_metadata, **kwargs):
        """Initialize a file."""
        parts = file_metadata["transfer"].get("parts", None)
        part_size = file_metadata["transfer"].get("part_size", None)
        size = file_metadata.get("size", None)
        checksum = file_metadata.get("checksum", None)
        storage_class = file_metadata.get("storage_class", None)

        if not parts:
            raise TransferException("Multipart file transfer requires parts.")

        if not size:
            raise TransferException("Multipart file transfer requires file size.")

        file_record = super().init_file(record, file_metadata)

        # create the object version and associated file instance that holds the storage_class
        version = ObjectVersion.create(record.bucket, file_record.key)
        file_record.object_version = version
        file_record.object_version_id = version.version_id

        self.uow.register(RecordCommitOp(file_record))

        # create the file instance that will be used to get the storage factory.
        # it might also be used to initialize the file (preallocate its size)
        file_instance = FileInstance.create()
        self.uow.register(ModelCommitOp(file_instance))
        version.set_file(file_instance)

        storage = self._get_storage(
            fileinstance=file_instance,
            default_location=(version.bucket.location.uri),
            default_storage_class=storage_class,
        )

        # ask the storage backend to initialize the upload
        multipart_metadata = (
            storage.multipart_initialize_upload(parts, size, part_size) or {}
        )
        multipart_metadata.setdefault("parts", parts)
        multipart_metadata.setdefault("part_size", part_size)
        multipart_metadata.setdefault("size", size)

        file_record.transfer["multipart_metadata"] = multipart_metadata

        # set the uri on the file instance and potentially the checksum
        file_instance.set_uri(
            storage.fileurl,
            size,
            checksum,
            storage_class=storage_class,
        )

        self.uow.register(ModelCommitOp(file_instance))
        self.uow.register(RecordCommitOp(file_record))
        return file_record

    def set_file_content(self, stream, content_length):
        """Set file content."""
        raise TransferException(
            "Can not set content for multipart file, use the parts instead."
        )

    def set_file_multipart_content(self, part, stream, content_length):
        """
        Set file content for a part.

        This method is called for each part of the
        multipart upload when the upload comes through the Invenio server (for example,
        the upload target is a local filesystem and not S3 or another external service).

        :param part: The part number.
        :param stream: The stream with the part content.
        :param content_length: The content length of the part. Must be equal to the
            part_size for all parts except the last one.
        """
        storage = self._get_storage()
        updated_multipart_metadata = storage.multipart_set_content(
            part, stream, content_length, **self.multipart_metadata
        )

        self.file_record.transfer["multipart_metadata"] = (
            updated_multipart_metadata or self.multipart_metadata
        )

    def commit_file(self):
        """
        Commit the file.

        This method is called after all parts have been uploaded.
        It then changes the storage class to local, thus turning the uploaded file
        into a file that can be sent via the configured storage backend.

        This is the same principle that Fetch uses to turn a file from a remote storage
        into a locally served one.
        """
        super().commit_file()

        storage = self._get_storage()
        checksum = storage.multipart_commit_upload(**self.multipart_metadata)

        recompute_checkum_needed = False

        file_instance = self.file_record.object_version.file
        if not file_instance.checksum:
            recompute_checkum_needed = True
            # get the multipart ETag and set it as the file checksum
            if checksum is not None:
                # set the checksum to the multipart checksum. This can later be picked
                # up by a background job to compute the whole-file checksum reliably.
                file_instance.checksum = (
                    f"multipart:{checksum}-{self.multipart_metadata['part_size']}"
                )
                self.uow.register(ModelCommitOp(file_instance))

        # change the transfer type to local
        self.file_record.transfer.transfer_type = LOCAL_TRANSFER_TYPE
        self.file_record.commit()

        if recompute_checkum_needed:
            self.uow.register(
                TaskOp(recompute_multipart_checksum_task, str(file_instance.id))
            )

    def delete_file(self):
        """If this method is called, we are deleting a file with an active multipart upload."""
        storage = self._get_storage()
        storage.multipart_abort_upload(**self.multipart_metadata)

    @property
    def status(self):
        """Get the status of the transfer."""
        # if the storage_class is M, return pending
        # after commit, the storage class is changed to L (same way as FETCH works)
        return TransferStatus.PENDING

    def expand_links(self, identity, self_url):
        """Expand links to include part urls."""
        # if the storage can expand links, use it
        storage = self._get_storage()
        return storage.multipart_links(self_url, **self.multipart_metadata)

    @property
    def multipart_metadata(self):
        """Get the multipart metadata."""
        return self.file_record.transfer["multipart_metadata"]

    def _get_storage(self, **kwargs):
        """Internal method to get the storage backend."""
        if "fileinstance" not in kwargs:
            kwargs["fileinstance"] = self.file_record.file
        # get the storage backend
        storage = current_files_rest.storage_factory(**kwargs)
        return MultipartStorageExt(storage)
