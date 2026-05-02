# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 CESNET.
# Copyright (C) 2026 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Local transfer provider."""

from flask_babel import gettext as _
from invenio_db.uow import ModelCommitOp
from invenio_files_rest import current_files_rest
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import FileInstance, ObjectVersion

from ....errors import TransferException
from ....uow import RecordCommitOp
from ..base import Transfer, TransferStatus
from ..constants import LOCAL_STAGED_TRANSFER_TYPE, LOCAL_TRANSFER_TYPE
from ..content import StagedContentHandle


class LocalTransfer(Transfer):
    """Local transfer.

    This transfers expects the file to be uploaded directly in one go to the
    server. The file content is stored in the record's bucket.
    """

    transfer_type = LOCAL_TRANSFER_TYPE

    def set_file_content(self, stream, content_length):
        """Set file content."""
        if self.file_record.file is not None:
            raise TransferException(
                _(f'File with key "{self.file_record.key}" is already committed.')
            )

        super().set_file_content(stream, content_length)


class StagedLocalTransfer(LocalTransfer):
    """Local transfer with prepare/transfer/finalize phases."""

    transfer_type = LOCAL_STAGED_TRANSFER_TYPE
    supports_staged_content = True

    def init_file(self, record, file_metadata, **kwargs):
        """Pre-allocate FileInstance and ObjectVersion bound to the FileRecord."""
        # FileInstance.create() returns a writable, not-yet-readable instance:
        # the reserved state we want. Both objects are created here so the
        # later phases (StagedContentHandle.write() and
        # StagedContentHandle.finalize()) have stable ids to work against
        # without further DB writes.
        file_instance = FileInstance.create()
        self.uow.register(ModelCommitOp(file_instance))

        version = ObjectVersion.create(
            record.bucket, file_metadata["key"], _file_id=file_instance
        )

        file_record = super().init_file(record, file_metadata, obj=version, **kwargs)
        self.uow.register(RecordCommitOp(file_record))
        return file_record

    def begin_content(self, content_length):
        """Validate state and return a :class:`StagedContentHandle`."""
        ov = self.file_record.object_version
        if ov is None or ov.file is None:
            raise TransferException(
                _(
                    f'Staged file "{self.file_record.key}" is missing pre-allocated state.'
                )
            )
        if ov.file.readable:
            raise TransferException(
                _(f'File with key "{self.file_record.key}" is already committed.')
            )

        bucket = self.record.bucket
        size_limit = bucket.size_limit
        if content_length and size_limit and content_length > size_limit:
            desc = (
                _("File size limit exceeded.")
                if isinstance(size_limit, int)
                else size_limit.reason
            )
            raise FileSizeError(description=desc)

        fi = ov.file
        storage = current_files_rest.storage_factory(
            fileinstance=fi,
            default_location=bucket.location.uri,
            default_storage_class=bucket.default_storage_class,
        )
        # The handle holds only plain values (ids, a storage object) and no
        # ORM references, so StagedContentHandle.write() can run after the
        # surrounding transaction has been committed.
        return StagedContentHandle(
            file_instance_id=fi.id,
            bucket_id=bucket.id,
            storage=storage,
            size_limit=size_limit,
            file_key=self.file_record.key,
        )

    def commit_file(self):
        """Commit the staged upload once finalize has marked the FileInstance readable."""
        # StagedContentHandle.finalize() flips FileInstance.readable to True
        # after the bytes are on disk. If it has not run, the FileInstance
        # is still in its reserved state and must not be promoted to a
        # committed file.
        ov = self.file_record.object_version
        fi = ov.file if ov is not None else None
        if fi is None or not fi.readable:
            raise TransferException(
                _(f'Staged upload for file "{self.file_record.key}" has not finalized.')
            )
        super().commit_file()

    @property
    def status(self):
        """Pending until the FileInstance is readable."""
        if self.file_record is None:
            return TransferStatus.PENDING
        ov = self.file_record.object_version
        if ov is None or ov.file is None or not ov.file.readable:
            return TransferStatus.PENDING
        return TransferStatus.COMPLETED
