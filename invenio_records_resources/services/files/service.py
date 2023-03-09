# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File Service API."""

from ..base import LinksTemplate, Service
from ..errors import FileKeyNotFoundError
from ..records.schema import ServiceSchemaWrapper
from ..uow import RecordCommitOp, unit_of_work


class FileService(Service):
    """A service for adding files support to records."""

    @property
    def record_cls(self):
        """Get the record class."""
        return self.config.record_cls

    @property
    def file_schema(self):
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.file_schema)

    def file_result_item(self, *args, **kwargs):
        """Create a new instance of the resource unit."""
        return self.config.file_result_item_cls(*args, **kwargs)

    def file_result_list(self, *args, **kwargs):
        """Create a new instance of the resource list."""
        return self.config.file_result_list_cls(*args, **kwargs)

    def file_links_list_tpl(self, id_):
        """Return a link template for list results."""
        return LinksTemplate(self.config.file_links_list, context={"id": id_})

    def file_links_item_tpl(self, id_):
        """Return a link template for item results."""
        return LinksTemplate(self.config.file_links_item, context={"id": id_})

    def check_permission(self, identity, action_name, **kwargs):
        """Check a permission against the identity."""
        action_name = self.config.permission_action_prefix + action_name
        return super().check_permission(identity, action_name, **kwargs)

    def _get_record(self, id_, identity, action, file_key=None):
        """Get the associated record.

        If a ``file_key`` is specified and the record in question doesn't have a file
        for that key, a ``FileKeyNotFoundError`` will be raised.
        """
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        self.require_permission(identity, action, record=record, file_key=file_key)

        if file_key and file_key not in record.files:
            raise FileKeyNotFoundError(id_, file_key)

        return record

    #
    # High-level API
    #
    def list_files(self, identity, id_):
        """List the files of a record."""
        record = self._get_record(id_, identity, "read_files")

        self.run_components("list_files", id_, identity, record)

        return self.file_result_list(
            self,
            identity,
            results=record.files.values(),
            record=record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def init_files(self, identity, id_, data, uow=None):
        """Initialize the file upload for the record."""
        record = self._get_record(id_, identity, "create_files")

        self.run_components("init_files", identity, id_, record, data, uow=uow)

        return self.file_result_list(
            self,
            identity,
            results=record.files.values(),
            record=record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def update_file_metadata(self, identity, id_, file_key, data, uow=None):
        """Update the metadata of a file.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(id_, identity, "create_files", file_key=file_key)

        self.run_components(
            "update_file_metadata", identity, id_, file_key, record, data, uow=uow
        )

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def read_file_metadata(self, identity, id_, file_key):
        """Read the metadata of a file.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(id_, identity, "read_files", file_key=file_key)

        self.run_components("read_file_metadata", identity, id_, file_key, record)

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def extract_file_metadata(self, identity, id_, file_key, uow=None):
        """Extract metadata from a file and update the file metadata file.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(id_, identity, "create_files", file_key=file_key)
        file_record = record.files[file_key]

        self.run_components(
            "extract_file_metadata",
            identity,
            id_,
            file_key,
            record,
            file_record,
            uow=uow,
        )

        uow.register(RecordCommitOp(file_record))

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def commit_file(self, identity, id_, file_key, uow=None):
        """Commit a file upload.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(id_, identity, "commit_files", file_key=file_key)

        self.run_components("commit_file", identity, id_, file_key, record, uow=uow)

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def delete_file(self, identity, id_, file_key, uow=None):
        """Delete a single file.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(id_, identity, "delete_files", file_key=file_key)
        deleted_file = record.files.delete(file_key)

        self.run_components(
            "delete_file", identity, id_, file_key, record, deleted_file, uow=uow
        )

        # We also commit the record in case the file was the `default_preview`
        uow.register(RecordCommitOp(record))

        return self.file_result_item(
            self,
            identity,
            deleted_file,
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def delete_all_files(self, identity, id_, uow=None):
        """Delete all the files of the record."""
        record = self._get_record(id_, identity, "delete_files")

        # We have to separate the gathering of the keys from their deletion
        # because of how record.files is implemented.
        file_keys = [fk for fk in record.files]
        results = [record.files.delete(file_key) for file_key in file_keys]

        self.run_components("delete_all_files", identity, id_, record, results, uow=uow)

        uow.register(RecordCommitOp(record))

        return self.file_result_list(
            self,
            identity,
            results,
            record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def set_file_content(
        self, identity, id_, file_key, stream, content_length=None, uow=None
    ):
        """Save file content.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(id_, identity, "set_content_files", file_key=file_key)

        self.run_components(
            "set_file_content",
            identity,
            id_,
            file_key,
            stream,
            content_length,
            record,
            uow=uow,
        )

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def get_file_content(self, identity, id_, file_key):
        """Retrieve file content.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(id_, identity, "get_content_files", file_key=file_key)

        self.run_components("get_file_content", identity, id_, file_key, record)

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )
