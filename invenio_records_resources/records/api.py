# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records API."""

from invenio_db import db
from invenio_files_rest.models import FileInstance, ObjectVersion
from invenio_records.api import Record as RecordBase
from invenio_records.dumpers import ElasticsearchDumper
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
    dumper = ElasticsearchDumper()

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
                cls.record_id == record_id, cls.key == key).one_or_none()
            if obj:
                return cls(obj.data, model=obj)

    @classmethod
    def list_by_record(cls, record_id):
        """List all record files by record ID."""
        for obj in cls.model_cls.query.filter(
                cls.model_cls.record_id == record_id):
            yield cls(obj.data, model=obj)

    @property
    def file(self):
        """File wrapper object."""
        if self.object_version:
            return File(object_model=self.object_version)

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
    dumper = ElasticsearchDumper()

    #: Metadata system field.
    metadata = DictField(clear_none=True, create_if_missing=True)

    key = ModelField()
    object_version_id = ModelField()
    object_version = ModelField(dump=False)
    record_id = ModelField()
    _record = ModelField('record', dump=False)

    def __repr__(self, ):
        """Represenation string for the record file."""
        return f"<{type(self).__name__}({self.key}, {self.metadata})"


class File:
    """File wrapper object."""

    def __init__(self, object_model=None, file_model=None):
        """Initialize the file wrapper object."""
        self.object_model = object_model
        self.file_model = file_model or object_model.file

    @classmethod
    def from_dict(cls, data, bucket):
        """Construct a file wrapper from a dictionary."""
        file_args = dict(
            id=data['file_id'],
            storage_class=data.get('storage_class'),
            size=data.get('size'),
            checksum=data.get('checksum'),
        )
        if 'uri' in data:
            file_args['uri'] = data['uri']

        fi = FileInstance(**file_args)
        obj = ObjectVersion(
            version_id=data['version_id'],
            key=data['key'],
            file_id=data['file_id'],
            _mimetype=data['mimetype'],
            is_head=True,
            bucket=bucket,
            bucket_id=data.get('bucket_id', bucket.id),
        )
        return cls(object_model=obj, file_model=fi)

    def dumps(self):
        """Dump file model attributes of the object."""
        return {
            'version_id': str(self.object_model.version_id),
            'key': self.object_model.key,
            'bucket_id': str(self.object_model.bucket_id),
            'file_id': str(self.object_model.file_id),
            'uri': str(self.object_model.file.uri),
            'storage_class': self.object_model.file.storage_class,
            'mimetype': self.object_model.mimetype,
            'size': self.object_model.file.size,
            'checksum': self.object_model.file.checksum,
        }

    def __getattr__(self, name):
        """Override to get attributes from ObjectVersion and FileInstance."""
        ret = getattr(self.object_model, name, None)
        if not ret:
            ret = getattr(self.file_model, name, None)
        if not ret:
            raise AttributeError
        return ret

    def __repr__(self):
        """Representation string for the file wrapper object."""
        return f"<{type(self).__name__}({self.key}, {self.file_id})"
