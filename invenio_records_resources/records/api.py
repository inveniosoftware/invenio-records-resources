# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2023 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records API."""

import mimetypes
from contextlib import contextmanager

from invenio_db import db
from invenio_files_rest.models import FileInstance, ObjectVersion
from invenio_records.api import Record as RecordBase
from invenio_records.dumpers import SearchDumper
from invenio_records.systemfields import DictField, SystemFieldsMixin
from invenio_records.systemfields.model import ModelField


class Record(RecordBase, SystemFieldsMixin):
    """Base class for record APIs.

    Subclass this record, and specify as minimum the ``model_cls`` class-level
    attribute.
    """

    #: Disable signals - we use record extensions instead (more precise).
    send_signals = False

    #: Disable JSONRef replacement (due to complexity of configuration).
    enable_jsonref = False

    #: Default model class used by the record API (specify in subclass).
    model_cls = None

    #: Default dumper (which happens to also be used for indexing).
    dumper = SearchDumper()

    #: Metadata system field.
    metadata = DictField(clear_none=True, create_if_missing=True)

    #: Concrete implementations need to implement the index field.
    # index = IndexField(...)

    #: Concrete implementations need to implement the files field.
    # files = FilesField(...)


class FileRecord(RecordBase, SystemFieldsMixin):
    """Base class for a record describing a file."""

    @classmethod
    def get_by_key(cls, record_id, key):
        """Get a record file by record ID and filename/key."""
        with db.session.no_autoflush:
            obj = cls.model_cls.query.filter(
                cls.record_id == record_id, cls.key == key
            ).one_or_none()
            if obj:
                return cls(obj.data, model=obj)

    @classmethod
    def list_by_record(cls, record_id):
        """List all record files by record ID."""
        for obj in cls.model_cls.query.filter(cls.model_cls.record_id == record_id):
            yield cls(obj.data, model=obj)

    @property
    def file(self):
        """File wrapper object."""
        if self.object_version:
            return File(object_model=self.object_version)

    @contextmanager
    def open_stream(self, mode):
        """Get a file stream for a given file record."""
        fp = self.object_version.file.storage().open(mode)
        try:
            yield fp
        finally:
            fp.close()

    def get_stream(self, mode):
        """Get a file stream for a given file record.

        It is up to the caller to close the steam.
        """
        return self.object_version.file.storage().open(mode)

    @property
    def record(self):
        """Get the file's record."""
        return self.record_cls(self._record.data, model=self._record)

    send_signals = False
    enable_jsonref = False

    #: Default model class used by the record API (specify in subclass).
    model_cls = None

    #: Record API class.
    record_cls = None

    #: Default dumper (which happens to also be used for indexing).
    dumper = SearchDumper()

    #: Metadata system field.
    metadata = DictField(clear_none=True, create_if_missing=True)

    key = ModelField()
    object_version_id = ModelField()
    object_version = ModelField(dump=False)
    record_id = ModelField()
    _record = ModelField("record", dump=False)

    def __repr__(
        self,
    ):
        """Represenation string for the record file."""
        return f"<{type(self).__name__}({self.key}, {self.metadata})"


class File:
    """File wrapper object."""

    def __init__(self, object_model=None, file_model=None):
        """Initialize the file wrapper object."""
        self.object_model = object_model
        self.file_model = file_model or object_model.file

    @classmethod
    def from_dump(cls, data):
        """Construct a file wrapper from a dictionary."""
        file_args = dict(
            id=data["file_id"],
            size=data.get("size"),
            checksum=data.get("checksum"),
        )
        fi = FileInstance(**file_args)
        obj = ObjectVersion(
            version_id=data["object_version_id"],
            key=data["key"],
            file_id=data["file_id"],
            file=fi,
            _mimetype=data["mimetype"],
            is_head=True,
            bucket_id=data["bucket_id"],
        )
        return cls(object_model=obj, file_model=fi)

    def dumps(self):
        """Dump file model attributes of the object."""
        data = {
            "checksum": self.object_model.file.checksum,
            "mimetype": self.object_model.mimetype,
            "size": self.object_model.file.size,
            "ext": self.ext,
            "object_version_id": str(self.object_model.version_id),
            "file_id": str(self.object_model.file_id),
        }
        return data

    @property
    def ext(self):
        """File extension."""
        ext = mimetypes.guess_extension(self.object_model.mimetype)
        return ext[1:] if ext else None

    def __getattr__(self, name):
        """Override to get attributes from ObjectVersion and FileInstance."""
        ret = getattr(self.object_model, name, None)
        if ret is None:
            ret = getattr(self.file_model, name, None)
        if ret is None:
            raise AttributeError
        return ret

    def __repr__(self):
        """Representation string for the file wrapper object."""
        return f"<{type(self).__name__}({self.key}, {self.file_id})"


class PersistentIdentifierWrapper:
    """Persistent Identifer wrapper object.

    It emulates a PID, but it is not stored in pidstore.
    It is normally used along with ModelPIDField.
    """

    def __init__(self, pid_value):
        """Constructor."""
        self.pid_value = pid_value
