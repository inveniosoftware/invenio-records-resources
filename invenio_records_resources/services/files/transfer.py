# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files transfer."""

from abc import ABC, abstractmethod
from enum import Enum

from invenio_db import db
from invenio_files_rest.errors import FileSizeError

from ..errors import TransferException
from ..uow import TaskOp
from .tasks import fetch_file


class TransferType(str, Enum):
    """File type, it inherits from str to be JSON serializable.

    LOCAL represents a file that is stored locally in the instance's storage.
    FETCH represents a file that needs to be fetched from an external storage
             and saved locally.
    REMOTE represents a file that is stored externally and is linked to the record.
    """

    LOCAL = "L"
    FETCH = "F"
    REMOTE = "R"

    def __eq__(self, other):
        """Equality test."""
        return self.value == other

    def __str__(self):
        """Return its value."""
        return self.value

    @property
    def is_completed(self):
        """Return if the type represents a completed transfer."""
        return self in [TransferType.LOCAL, TransferType.REMOTE]

    def is_serializable(self):
        """Return if the type represents a localy available file."""
        return self != TransferType.LOCAL


class BaseTransfer(ABC):
    """Local transfer."""

    def __init__(self, type, service=None, uow=None):
        """Constructor."""
        self.type = type
        self.service = service
        self.uow = uow

    @abstractmethod
    def init_file(self, record, file_metadata):
        """Initialize a file."""
        raise NotImplementedError()

    def set_file_content(self, record, file, file_key, stream, content_length):
        """Set file content."""
        bucket = record.bucket
        size_limit = bucket.size_limit
        if content_length and size_limit and content_length > size_limit:
            desc = (
                "File size limit exceeded."
                if isinstance(size_limit, int)
                else size_limit.reason
            )
            raise FileSizeError(description=desc)

        record.files.create_obj(
            file_key, stream, size=content_length, size_limit=size_limit
        )

    def commit_file(self, record, file_key):
        """Commit a file."""
        # fetch files can be committed, its up to permissions to decide by who
        # e.g. system, since its the one downloading the file
        record.files.commit(file_key)

    # @abstractmethod
    # def read_file_content(self, record, file_metadata):
    #     """Read a file content."""
    #     pass


class LocalTransfer(BaseTransfer):
    """Local transfer."""

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(TransferType.LOCAL, **kwargs)

    def init_file(self, record, file_metadata):
        """Initialize a file."""
        uri = file_metadata.pop("uri", None)
        if uri:
            raise Exception("Cannot set URI for local files.")

        file = record.files.create(key=file_metadata.pop("key"), data=file_metadata)

        return file

    def set_file_content(self, record, file, file_key, stream, content_length):
        """Set file content."""
        if file:
            raise TransferException(f'File with key "{file_key}" is committed.')

        super().set_file_content(record, file, file_key, stream, content_length)


class FetchTransfer(BaseTransfer):
    """Fetch transfer."""

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(TransferType.FETCH, **kwargs)

    def init_file(self, record, file_metadata):
        """Initialize a file."""
        uri = file_metadata.pop("uri", None)
        if not uri:
            raise Exception("URI is required for fetch files.")

        obj_kwargs = {
            "file": {
                "uri": uri,
                "storage_class": self.type,
                "checksum": file_metadata.pop("checksum", None),
                "size": file_metadata.pop("size", None),
            }
        }

        file_key = file_metadata.pop("key")
        file = record.files.create(
            key=file_key,
            data=file_metadata,
            obj=obj_kwargs,
        )

        self.uow.register(
            TaskOp(
                fetch_file,
                service_id=self.service.id,
                record_id=record.pid.pid_value,
                file_key=file_key,
            )
        )
        return file


class Transfer:
    """Transfer type."""

    @classmethod
    def get_transfer(cls, file_type, **kwargs):
        """Get transfer type."""
        if file_type == TransferType.FETCH:
            return FetchTransfer(**kwargs)
        else:  # default to local
            return LocalTransfer(**kwargs)

    @classmethod
    def commit_file(cls, record, file_key):
        """Commit a file."""
        file = record.files.get(file_key).file
        transfer = cls.get_transfer(getattr(file, "storage_class", None))
        # file is not passed since that is the current head of the OV
        # committing means setting the latest of the bucket (OV.get)
        transfer.commit_file(record, file_key)
