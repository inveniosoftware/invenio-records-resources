# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2023 CERN.
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
        # Persisted when `store=True`
        'count': 1,
        'totalbytes': 12345,
        'mimetypes': ['application/pdf'],
        'types': ['pdf'],
        'entries': {
            'paper.pdf': {
                'uuid': '<file-record-id>',
                'version_id': '<file-record-version-id>',
                'object_version_id': '<object-version-id>',
                'metadata': {...},
                'file_id': '<file-id>,
                'key': 'paper.pdf',
                'ext': 'pdf',
                'mimetype': 'application/pdf',
                'size': 12345,
                'checksum': 'md5:abcdef...',
            },
        }
    }
}
"""

from invenio_records.systemfields import SystemField

from ....services.records.components.files import FilesAttrConfig
from ...dumpers import PartialFileDumper
from .manager import FilesManager


class FilesField(SystemField):
    """Files system field."""

    def __init__(
        self,
        key=FilesAttrConfig["_files_attr_key"],
        bucket_id_attr=FilesAttrConfig["_files_bucket_id_attr_key"],
        bucket_attr=FilesAttrConfig["_files_bucket_attr_key"],
        store=True,
        dump=False,
        dump_entries=True,
        file_cls=None,
        enabled=True,
        bucket_args=None,
        create=True,
        delete=True,
    ):
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
        self._dump = dump
        self._dump_entries = dump_entries
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
        return self._file_cls or getattr(self.record, "file_cls", None)

    #
    # Life-cycle hooks
    #
    def pre_commit(self, record):
        """Called before a record is committed."""
        # Make sure we serialize the files on record.commit() time as they
        # might have changed.
        files = getattr(record, self.attr_name)
        if files is not None:
            self.store(record, files)

    def post_create(self, record):
        """Called after a record is created."""
        files = FilesManager(
            record,
            file_cls=self.file_cls,
            enabled=self._enabled,
            options=self._manager_options,
        )

        if self._create and self._enabled:
            files.create_bucket()

        self.store(record, files)

    def post_dump(self, record, data, **kwargs):
        """Called after a record is dumped in a secondary storage system."""
        # Dump files into index if requested (if store=True, files are already
        # part of the dumped record)
        if self._dump and not self._store:
            files = getattr(record, self.attr_name)
            if files is not None:
                # Determine if entries should be included.
                # Use to remove file entries from search dump in case a record
                # is public but files are restricted.
                if callable(self._dump_entries):
                    include_entries = self._dump_entries(record)
                else:
                    include_entries = self._dump_entries

                self.set_dictkey(
                    data, self.dump(record, files, include_entries=include_entries)
                )

        # Prepare file entries for index (dict to list)
        if self._dump or self._store:
            files = self.get_dictkey(data)
            if "entries" in files:
                files["entries"] = list(files["entries"].values())

    def pre_load(self, data, loader=None):
        """Called before a record is loaded."""
        if self._dump or self._store:
            # Undo dict to list transform from post_dump().
            files = self.get_dictkey(data)
            if "entries" in files:
                files["entries"] = {f["key"]: f for f in files["entries"]}

    def post_load(self, record, data, loader=None):
        """Called after a record is loaded."""
        file_data = self.get_dictkey(record)
        if file_data:
            self._set_cache(record, self.load(record, file_data, from_dump=True))
            if not self._store:
                file_data.pop("count", None)
                file_data.pop("mimetypes", None)
                file_data.pop("totalbytes", None)
                file_data.pop("types", None)
                file_data.pop("entries", None)

    def post_delete(self, record, force=False):
        """Called after a record is deleted."""
        if self._delete:
            files = getattr(record, self.attr_name)
            if files is not None:
                files.remove_bucket(force=force)

    @property
    def _manager_options(self):
        """Return options for the manager."""
        return {
            "bucket_id_attr": self._bucket_id_attr,
            "bucket_attr": self._bucket_attr,
            "bucket_args": self._bucket_args,
        }

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
            obj = self.load(record, data)
            self._set_cache(record, obj)
            return obj
        return None

    def load(self, record, data, from_dump=False):
        """Create a file manager from a record and data."""
        entries = None
        if self._store or from_dump:
            # If file entries where stored in the database record, or dumped
            # into the index they will be loaded here.
            entries = {}
            for key, file_data in data.get("entries", {}).items():
                # Inject record_id/bucket_id here to avoid storing it
                # redundantly for each file.
                file_data["record_id"] = record.id
                file_data["bucket_id"] = getattr(record, self._bucket_id_attr)
                entries[key] = self.file_cls.loads(
                    file_data, loader=PartialFileDumper()
                )

        return FilesManager(
            record=record,
            file_cls=self.file_cls,
            enabled=data.get("enabled", self._enabled),
            order=data.get("order", []),
            default_preview=data.get("default_preview"),
            entries=entries,
            options=self._manager_options,
        )

    def dump(self, record, files, include_entries=False):
        """Dump a file manager."""
        data = {
            "enabled": files.enabled,
        }

        if files.order:
            data["order"] = files.order
        if files.default_preview:
            data["default_preview"] = files.default_preview
        if include_entries and files.enabled:
            data["count"] = len(files)
            data["mimetypes"] = files.mimetypes
            data["totalbytes"] = files.total_bytes
            data["types"] = files.exts
            data["entries"] = {}
            for file_record in files.values():
                data["entries"][file_record.key] = file_record.dumps(
                    dumper=PartialFileDumper()
                )
        return data

    def store(self, record, files):
        """Set the object."""
        data = self.dump(record, files, include_entries=self._store)
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
