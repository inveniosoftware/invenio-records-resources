# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files field.

The FilesField manages connected files to a record. This information is not
necessarily persisted in the metadata.

.. code-block:: python

{
    'files': {
        'enabled': True,
        'default_preview': 'paper.pdf',
        'order': [
            'paper.pdf',
            'figure.png',
            'data.zip',
        ],
        'meta': {
            'figure.png': {
                'description': 'Figure 1.1',
                'width': 512,
                'height': 256,
            }
        },
        # Persisted when `store=True`
        'bucket': {
            'quota_size': 200000,
            'max_file_size': 200000,
            'size': 15000,
            ...
        },
        'entries': {
            'paper.pdf': {
                'version_id': '<object-version-id>',
                'bucket_id': '<bucket-id>',
                'file_id': '<file-id>,
                'storage_class': 'A'
                'key': 'paper.pdf',
                'mimetype': 'application/pdf',
                'size': 12345,
                'checksum': 'md5:abcdef...',
            },
            'data.zip': {...},
            'figure.png': {...},
            ...
        }
    }
}
"""

from collections.abc import MutableMapping
from functools import wraps

from invenio_db import db
from invenio_files_rest.models import Bucket, FileInstance, ObjectVersion
from invenio_records.systemfields import SystemField


def ensure_enabled(func):
    """Decorator for ensuring that a FilesField is enabled."""
    @wraps(func)
    def inner(self, *args, **kwargs):
        if not self.enabled:
            raise Exception('Files are not enabled.')
        return func(self, *args, **kwargs)
    return inner


class Files(MutableMapping):
    """Files management dict-like wrapper."""

    def __init__(self, record, file_cls=None, bucket=None, enabled=True,
                 order=None, default_preview=None, entries=None):
        """Initialize the files collection."""
        self.record = record
        self.file_cls = file_cls
        self._bucket = bucket or record.bucket

        self._enabled = enabled
        self._order = order or []
        self._default_preview = default_preview

        self._entries = entries

    def _init(self, key, data=None):
        f = self.file_cls.create({}, key=key, record_id=self.record.id)
        if data:
            f.metadata = data
        return f

    @ensure_enabled
    def init(self, key, data):
        """Initialize a file."""
        if key in self:
            raise Exception(f'File with key {key} already exists.')

        f = self._init(key, data)
        self._entries[key] = f
        return f

    @ensure_enabled
    def create(self, key, stream, data):
        """Create a file."""
        if key in self:
            raise Exception(f'File with key {key} already exists.')

        f = self._init(key, data)
        obj = ObjectVersion.create(self.bucket, key, stream=stream)
        f.object_version_id = obj.version_id
        f.object_version = obj
        self._entries[key] = f
        return f

    @ensure_enabled
    def delete(self, key):
        """Delete a file."""
        # TODO: implement
        # f = self.entries[key]
        # f.delete()
        pass

    @property
    def entries(self):
        """Return file entries dictionary."""
        if self._entries is None:
            self._entries = {}
            for rf in self.file_cls.list_by_record(self.record.id):
                self._entries[rf.key] = rf
        return self._entries

    @property
    def bucket_id(self):
        """Return files bucket ID."""
        return self._bucket.id

    @property
    def bucket(self):
        """Return files bucket."""
        return self._bucket

    @property
    def enabled(self):
        """Return if files are enabled/disabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        """Enable/disable files."""
        if value is False:
            self.default_preview = None
            self.order = []
            # TODO: Delete or "empty" the bucket?
            self.bucket.delete()
        self._enabled = value

    @property
    def default_preview(self):
        """Get default preview file."""
        return self._default_preview

    @default_preview.setter
    def default_preview(self, key):
        """Set default preview file."""
        if key and key not in self:
            raise Exception(f'No file with key "{key}"')
        self._default_preview = key

    @property
    def order(self):
        """Get order of files."""
        return self._order

    @order.setter
    def order(self, new_order):
        """Set the order of the files."""
        for k in new_order:
            if k not in self:
                raise Exception(f'File with key "{k}" does not exist')
        self._order = new_order

    @ensure_enabled
    def __getitem__(self, key):
        """Get a file by key/filename."""
        value = self.entries.get(key)
        if isinstance(value, self.file_cls):
            return value
        # TODO: implement "file_cls.loads/from_dict"
        # elif isinstance(value, dict):
        #     return value
        else:  # fetch from db...
            value = self.file_cls.get_by_key(self.record.id, key)
            if value:
                self._entries[key] = value
                return value
        raise KeyError(f'No file with key "{key}"')

    @ensure_enabled
    def __setitem__(self, key, value):
        """Create or init a file.

        :param key: Filename.
        :param value: File-like object (stream), ``dict``, or a
            ``Tuple[File, Dict]``.
        """
        if isinstance(value, (tuple, list)):
            assert len(value) == 2
            stream, data = value
            assert hasattr(stream, 'read')
            assert isinstance(data, dict)
        else:
            if hasattr(value, 'read'):
                stream, data = value, None
            elif isinstance(value, dict):
                stream, data = None, value
            else:
                raise Exception(f"Invalid set value: {value}.")

        old_value = self.get(key)
        if stream:
            if old_value:
                obj = ObjectVersion.create(self.bucket, key, stream=stream)
                old_value.object_version_id = obj.version_id
                old_value.object_version = obj
                if data:
                    old_value.metadata = data
            else:
                self.create(key, stream, data)
        else:
            if old_value:
                old_value.metadata = data
            else:
                self.init(key, data)

    @ensure_enabled
    def __delitem__(self, key):
        """Delete a file."""
        # TODO: Make this configurable?
        # Unset the default preview if the file is removed
        if self.default_preview == key:
            self.default_preview = None
        self.delete(key)
        del self.entries[key]

    # TODO: implement for efficiency?
    # @ensure_enabled
    # def __contains__(self, key):
    #     return key in self.entries

    @ensure_enabled
    def __iter__(self):
        """File keys iterator."""
        return iter(self.entries)

    @ensure_enabled
    def __len__(self):
        """Count of files."""
        return len(self.entries)

    # TODO: see what fields are meaningful
    def __repr__(self):
        """Represenation string for the files collection."""
        return f"<{type(self).__name__} (enabled={self.enabled})"


class FilesField(SystemField):
    """Files system field."""

    def __init__(self, key='files', store=True, file_cls=None, enabled=True,
                 bucket_id_attr='bucket_id', bucket_attr='bucket',
                 bucket_args=None, create=True, delete=True):
        """Initialize the FilesField.

        :param key: Name of key to store the files metadata in.
        :param store: Set to ``True`` if files should be stored in the record's
            metadata.
        :param create: Set to True if files bucket should be automatically
            created.
        :param delete: Set to True if files bucket should be automatically
            deleted.
        """
        self._store = store
        self._enabled = enabled
        self._bucket_id_attr = bucket_id_attr
        self._bucket_attr = bucket_attr
        self._bucket_args = bucket_args or {}
        self._create = create
        self._delete = delete
        self._file_cls = file_cls
        super().__init__(key=key)

    @property
    def file_cls(self):
        """Record file class."""
        return self._file_cls or getattr(self.record, 'file_cls', None)

    #
    # Life-cycle hooks
    #
    def pre_commit(self, record):
        """Called before a record is committed."""
        # Make sure we serialize the files on record.commit() time as they
        # might have changed.
        files = getattr(record, self.attr_name)
        # XXX: merge all objects in the session?
        if files is not None:
            self.store(record, files)

    def post_create(self, record):
        """Called after a record is created."""
        if self._create and self._enabled:
            # This uses the data descriptor method __get__() below:
            if getattr(record, self.attr_name) is None:
                # Create a bucket if the object doesn't already have one.
                if callable(self._bucket_args):
                    # TODO: Document callable params
                    bucket_args = self._bucket_args(field=self, record=record)
                else:
                    bucket_args = self._bucket_args
                bucket = Bucket.create(**bucket_args)
                setattr(record, self._bucket_id_attr, bucket.id)
                setattr(record, self._bucket_attr, bucket)
        self.store(record, Files(
            record,
            file_cls=self.file_cls,
            enabled=self._enabled,
        ))

    def post_delete(self, record, force=False):
        """Called after a record is deleted."""
        if self._delete:
            files = getattr(record, self.attr_name)
            if files is not None:
                # TODO: Check if this is all that's needed
                bucket = record.bucket
                record.bucket = None
                record.bucket_id = None
                bucket.remove()

    #
    # Helpers
    #
    def obj(self, instance):
        """Get the files object."""
        obj = self._get_cache(instance)
        if obj:
            return obj
        data = self.get_dictkey(instance)

        if data:
            obj = Files(
                record=instance,
                file_cls=self.file_cls,
                enabled=data.get('enabled', self._enabled),
                order=data.get('order'),
                default_preview=data.get('default_preview'),
                entries=data.get('entries', {}) if self._store else None,
            )
            self._set_cache(instance, obj)
            return obj
        return None

    def store(self, record, files):
        """Set the object."""
        data = {
            'enabled': files.enabled,
            'order': files.order,
            'default_preview': files.default_preview,
        }

        if self._store and files.enabled:
            data['entries'] = {}
            # TODO: Does it make sense now to store separately? We can still
            # include `meta` in each entries object (since storage is now in
            # the RecordFile model)
            data['meta'] = {}

            for key, rf in files.items():
                if rf.file:
                    data['entries'][key] = rf.file.dumps()
                # TODO: rf.dumps() might be enough as well...
                data['meta'][key] = rf.metadata

        # Store data values on the attribute name (e.g. 'files')
        self.set_dictkey(record, data)
        self._set_cache(record, files)

    #
    # Data descriptor methods (i.e. attribute access)
    #
    def __get__(self, record, owner=None):
        """Get the record's files."""
        if record is None:
            return self
        return self.obj(record)

    # TODO: should `record.files = ...` be possible? Probably not...
    # def __set__(self, record, files):
    #     """Set files on a record."""
    #     raise Exception('Not possible to set.')
