# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files field.

The FilesField manages files connected to a record. This information is not
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

from invenio_files_rest.models import Bucket
from invenio_records.systemfields import SystemField

from .manager import FilesManager


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
    # TODO: Add support for pre_dump/post_load method so that files can be
    # searched - e.g. files.types:pdf files.size>:10000
    def pre_commit(self, record):
        """Called before a record is committed."""
        # Make sure we serialize the files on record.commit() time as they
        # might have changed.
        files = getattr(record, self.attr_name)
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
                if not (getattr(record, self._bucket_id_attr, None) and
                        getattr(record, self._bucket_attr, None)):
                    # TODO: Setting these bumps the row's `revision_id`
                    setattr(record, self._bucket_id_attr, bucket.id)
                    setattr(record, self._bucket_attr, bucket)
        self.store(record, FilesManager(
            record,
            file_cls=self.file_cls,
            enabled=self._enabled,
        ))

    def post_delete(self, record, force=False):
        """Called after a record is deleted."""
        if self._delete:
            files = getattr(record, self.attr_name)
            if files is not None:
                if record.bucket:
                    bucket = record.bucket
                    if force:
                        record.bucket = None
                        record.bucket_id = None
                        bucket.remove()
                    else:
                        Bucket.delete(bucket.id)

    #
    # Helpers
    #
    def obj(self, record):
        """Get the files object."""
        obj = self._get_cache(record)
        if obj is not None:
            return obj
        data = self.get_dictkey(record)
        if data:
            obj = FilesManager(
                record=record,
                file_cls=self.file_cls,
                enabled=data.get('enabled', self._enabled),
                order=data.get('order', []),
                default_preview=data.get('default_preview'),
                entries=data.get('entries', {}) if self._store else None,
            )
            self._set_cache(record, obj)
            return obj
        return None

    def store(self, record, files):
        """Set the object."""
        data = {
            'enabled': files.enabled,
        }
        if files.order:
            data['order'] = files.order
        if files.default_preview:
            data['default_preview'] = files.default_preview

        if self._store and files.enabled:
            data['entries'] = {}
            # TODO: Does it make sense now to store separately? We can still
            # include `meta` in each entries object (since storage is now in
            # the FileRecord model)
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
    # - might be interesting from the record->draft or draft-> record POW
    # def __set__(self, record, files):
    #     """Set files on a record."""
    #     raise Exception('Not possible to set.')
