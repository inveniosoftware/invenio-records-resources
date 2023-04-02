# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2023 CERN.
# Copyright (C) 2020-2021 Northwestern University.
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

from invenio_files_rest.errors import InvalidKeyError, InvalidOperationError
from invenio_files_rest.models import Bucket, FileInstance, ObjectVersion

from ...dumpers import PartialFileDumper


def ensure_enabled(func):
    """Decorator for ensuring that a FilesField is enabled."""

    @wraps(func)
    def inner(self, *args, **kwargs):
        if not self.enabled:
            raise InvalidOperationError(description="Files are not enabled.")
        return func(self, *args, **kwargs)

    return inner


class FilesManager(MutableMapping):
    """Files management dict-like wrapper."""

    def __init__(
        self,
        record,
        file_cls=None,
        bucket=None,
        enabled=True,
        order=None,
        default_preview=None,
        entries=None,
        options=None,
    ):
        """Initialize the files collection."""
        self._options = options or {}
        self.record = record
        self.file_cls = file_cls
        self._bucket = bucket or getattr(record, self._options["bucket_attr"], "bucket")

        self._enabled = enabled
        self._order = order or []
        self._default_preview = default_preview
        self._entries = entries

    def create_bucket(self):
        """Create a bucket."""
        # Create a bucket if the object doesn't already have one.
        bucket_args = self._options["bucket_args"]
        if callable(bucket_args):
            # TODO: Document callable params
            bucket_args = bucket_args(record=self.record)

        self.set_bucket(Bucket.create(**bucket_args))

    def remove_bucket(self, force=False):
        """Remove the bucket."""
        if self.bucket:
            bucket = self.bucket
            self.unset_bucket()
            # TODO: not sure this makes sense???
            if force:
                bucket.remove()
            else:
                Bucket.delete(bucket.id)

    def unset_bucket(self):
        """Unassign the bucket from the record."""
        setattr(self.record, self._options["bucket_attr"], None)
        setattr(self.record, self._options["bucket_id_attr"], None)
        self._bucket = None

    def set_bucket(self, bucket, overwrite=False):
        """Set the bucket on the record."""
        # TODO: Setting these bumps the row's `revision_id`
        setattr(self.record, self._options["bucket_attr"], bucket)
        setattr(self.record, self._options["bucket_id_attr"], bucket.id)
        self._bucket = bucket

    def lock(self):
        """Lock the bucket."""
        self.bucket.locked = True

    def unlock(self):
        """Unlock the bucket."""
        self.bucket.locked = False

    # TODO: "create" and "update" should be merged somehow...
    @ensure_enabled
    def create(self, key, obj=None, stream=None, data=None, **kwargs):
        """Create/initialize a file."""
        assert not (obj and stream)

        if key in self:
            raise InvalidKeyError(description=f"File with key {key} already exists.")

        rf = self.file_cls.create({}, key=key, record_id=self.record.id)
        if stream:
            obj = ObjectVersion.create(self.bucket, key, stream=stream, **kwargs)
        if obj:
            if isinstance(obj, dict):
                fi = FileInstance.create()
                fi.set_uri(**obj.pop("file"))
                obj = ObjectVersion.create(self.bucket, key, fi.id)
            rf.object_version_id = obj.version_id
            rf.object_version = obj
        if data:
            rf.metadata = data
        rf.commit()
        self._entries[key] = rf
        return rf

    @ensure_enabled
    def create_obj(self, key, stream, data=None, **kwargs):
        """Create an ObjectVersion but do not pop it to the top of the stack."""
        # this is used on set_file_content, since the file is not yet commited
        rf = self.get(key)
        if rf is None:
            raise InvalidKeyError(description=f"File with {key} does not exist.")

        return ObjectVersion.create(self.bucket, key, stream=stream, **kwargs)

    @ensure_enabled
    def update(self, key, obj=None, stream=None, data=None, **kwargs):
        """Update a file."""
        assert not (obj and stream)
        rf = self.get(key)

        if stream:
            obj = self.create_obj(key, stream=stream, **kwargs)
        if obj:
            rf.object_version_id = obj.version_id
            rf.object_version = obj
        if data:
            rf.metadata = data
            rf.commit()
        return rf

    @ensure_enabled
    def commit(self, file_key):
        """Commit a file."""
        file_obj = ObjectVersion.get(self.bucket.id, file_key)
        if not file_obj:
            raise Exception(f"File with key {file_key} not uploaded yet.")
        self[file_key] = file_obj

    @ensure_enabled
    def delete(self, key, remove_obj=True, softdelete_obj=False):
        """Delete a file."""
        rf = self[key]
        ov = rf.object_version

        # Delete the entire row
        rf.delete(force=True)
        if ov and remove_obj:
            if remove_obj:
                rf.object_version.remove()
            elif softdelete_obj:
                ObjectVersion.delete(rf.object_version.bucket, rf.object_version.key)
        del self._entries[key]

        # Unset the default preview if the file is removed
        if self.default_preview == key:
            self.default_preview = None
        if key in self._order:
            self._order.remove(key)
        return rf

    @ensure_enabled
    def delete_all(self, remove_obj=True):
        """Delete all file records."""
        for key in list(self.keys()):
            self.delete(key, remove_obj=remove_obj)

    def copy(self, src_files, copy_obj=True):
        """Copy from another file manager."""
        self.enabled = src_files.enabled

        if not self.enabled:
            return

        for key, rf in src_files.items():
            # Copy object version of link existing?
            if copy_obj:
                dst_obj = rf.object_version.copy(bucket=self.bucket)
            else:
                dst_obj = rf.object_version

            # Copy file record
            if rf.metadata is not None:
                self[key] = dst_obj, rf.metadata
            else:
                self[key] = dst_obj

        self.default_preview = src_files.default_preview
        self.order = src_files.order

    def sync(self, src_files):
        """Sync changes from source files to this manager."""
        self.default_preview = src_files.default_preview
        self.order = src_files.order

        # TODO: We don't yet sync file additions/removals/changes from
        # "src_files". This should take into account if the current bucket
        # is locked or not.

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
        if value is False and self.enabled:
            self.default_preview = None
            self.order = []
            self.clear()
        self._enabled = value

    @property
    def count(self):
        """Return total number of files."""
        return len(self)

    @property
    def total_bytes(self):
        """Return total number of bytes."""
        return sum([f.file.size for f in self.entries.values() if f.file])

    @property
    def mimetypes(self):
        """Return list of mimetypes."""
        return list({f.file.mimetype for f in self.entries.values() if f.file})

    @property
    def exts(self):
        """Return list file extensions."""
        return list(
            {
                f.file.ext
                for f in self.entries.values()
                if f.file and f.file.ext is not None
            }
        )

    @property
    def default_preview(self):
        """Get default preview file."""
        return self._default_preview

    @default_preview.setter
    def default_preview(self, key):
        """Set default preview file."""
        if key and key not in self:
            raise InvalidKeyError(description=f'No file with key "{key}"')
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
                raise InvalidKeyError(description=f'File with key "{k}" does not exist')
        self._order = new_order

    @ensure_enabled
    def __getitem__(self, key):
        """Get a file by key/filename."""
        value = self.entries.get(key)
        if isinstance(value, self.file_cls):
            return value
        else:  # fetch from db...
            value = self.file_cls.get_by_key(self.record.id, key)
            if value:
                self._entries[key] = value
                return value
        raise KeyError(f'No file with key "{key}"')

    def _parse_set_value(self, value):
        obj, stream, data = None, None, None
        # TODO: Raise appropriate exceptions instead of asserting
        obj_or_stream = None
        if isinstance(value, (tuple, list)):
            assert len(value) == 2
            obj_or_stream, data = value
            assert isinstance(data, dict)
        elif isinstance(value, dict):
            data = value
        elif isinstance(value, ObjectVersion):
            obj = value
        elif hasattr(value, "read"):
            stream = value
        else:
            raise Exception(f"Invalid set value: {value}")

        if obj_or_stream:
            if isinstance(obj_or_stream, ObjectVersion):
                obj = obj_or_stream
            elif hasattr(obj_or_stream, "read"):
                stream = obj_or_stream
            else:
                raise InvalidOperationError(
                    description=f"Item has to be ObjectVersion or " "file-like object"
                )

        return obj, stream, data

    @ensure_enabled
    def __setitem__(self, key, value):
        """Create or init a file.

        :param key: Filename.
        :param value: File-like object (stream), ``dict``, or a
            ``Tuple[File, Dict]``.
        """
        obj, stream, data = self._parse_set_value(value)

        if key in self:
            self.update(key, obj=obj, stream=stream, data=data)
        else:
            self.create(key, obj=obj, stream=stream, data=data)

    @ensure_enabled
    def __delitem__(self, key):
        """Delete a file."""
        # TODO: Make this configurable?
        self.delete(key)

    @ensure_enabled
    def __iter__(self):
        """File keys iterator."""
        return iter(self.entries)

    def __len__(self):
        """Count of files."""
        return len(self.entries)

    # TODO: see what fields are meaningful
    def __repr__(self):
        """Represenation string for the files collection."""
        return f"<{type(self).__name__} (enabled={self.enabled})"
