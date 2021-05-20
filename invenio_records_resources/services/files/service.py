# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File Service API."""

from invenio_db import db

from ..base import LinksTemplate, Service
from ..records.schema import ServiceSchemaWrapper


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
        return LinksTemplate(
            self.config.file_links_list, context={"id": id_}
        )

    def file_links_item_tpl(self, id_):
        """Return a link template for item results."""
        return LinksTemplate(
            self.config.file_links_item, context={"id": id_}
        )

    def check_permission(self, identity, action_name, **kwargs):
        """Check a permission against the identity."""
        action_name = self.config.permission_action_prefix + action_name
        return super().check_permission(identity, action_name, **kwargs)

    def get_record(self, id_, identity, action):
        """Get the associated record."""
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        self.require_permission(identity, action, record=record)
        return record

    #
    # High-level API
    #
    def list_files(self, id_, identity):
        """List the files of a record."""
        record = self.get_record(id_, identity, "read_files")

        self.run_components("list_files", id_, identity, record)

        return self.file_result_list(
            self,
            identity,
            results=record.files.values(),
            record=record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    def init_files(self, id_, identity, data):
        """Initialize the file upload for the record."""
        record = self.get_record(id_, identity, "create_files")

        self.run_components("init_files", id_, identity, record, data)

        db.session.commit()

        self.run_components("post_init_files", id_, identity, record, data)

        return self.file_result_list(
            self,
            identity,
            results=record.files.values(),
            record=record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    def update_file_metadata(self, id_, file_key, identity, data):
        """Update the metadata of a file."""
        record = self.get_record(id_, identity, "create_files")

        self.run_components(
            "update_file_metadata", id_, file_key, identity, record, data)

        db.session.commit()

        self.run_components(
            "post_update_file_metadata", id_, file_key, identity, record, data)

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def read_file_metadata(self, id_, file_key, identity):
        """Read the metadata of a file."""
        record = self.get_record(id_, identity, "read_files")

        self.run_components(
            "read_file_metadata", id_, file_key, identity, record)

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def extract_file_metadata(self, id_, file_key, identity):
        """Extract metadata from a file and update the file metadata file."""
        record = self.get_record(id_, identity, "create_files")
        file_record = record.files[file_key]

        self.run_components(
            "extract_file_metadata", id_, file_key, identity, record,
            file_record)

        file_record.commit()
        db.session.commit()

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def commit_file(self, id_, file_key, identity):
        """Commit a file upload."""
        record = self.get_record(id_, identity, "create_files")

        self.run_components("commit_file", id_, file_key, identity, record)

        db.session.commit()

        self.run_components(
            "post_commit_file", id_, file_key, identity, record)

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def delete_file(self, id_, file_key, identity):
        """Delete a single file."""
        record = self.get_record(id_, identity, "delete_files")
        deleted_file = record.files.delete(file_key)

        self.run_components(
            "delete_file", id_, file_key, identity, record, deleted_file)

        # We also commit the record in case the file was the `default_preview`
        record.commit()
        db.session.commit()

        self.run_components(
            "post_delete_file", id_, file_key, identity, record, deleted_file)

        return self.file_result_item(
            self,
            identity,
            deleted_file,
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def delete_all_files(self, id_, identity):
        """Delete all the files of the record."""
        record = self.get_record(id_, identity, "delete_files")

        # We have to separate the gathering of the keys from their deletion
        # because of how record.files is implemented.
        file_keys = [fk for fk in record.files]
        results = [record.files.delete(file_key) for file_key in file_keys]

        self.run_components("delete_all_files", id_, identity, record, results)

        record.commit()
        db.session.commit()

        self.run_components(
            "post_delete_all_files", id_, identity, record, results)

        return self.file_result_list(
            self,
            identity,
            results,
            record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    def set_file_content(
            self, id_, file_key, identity, stream, content_length=None):
        """Save file content."""
        record = self.get_record(id_, identity, "create_files")

        self.run_components(
            "set_file_content", id_, file_key, identity, stream,
            content_length, record)

        db.session.commit()

        self.run_components(
            "post_set_file_content", id_, file_key, identity, stream,
            content_length, record
        )

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def get_file_content(self, id_, file_key, identity):
        """Retrieve file content."""
        record = self.get_record(id_, identity, "read_files")

        self.run_components(
            "get_file_content", id_, file_key, identity, record)

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )
