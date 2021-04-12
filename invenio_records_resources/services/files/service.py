# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File Service API."""

from copy import deepcopy

from invenio_db import db
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import ObjectVersion

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

    #
    # High-level API
    #
    def list_files(self, id_, identity):
        """List the files of a record."""
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        self.require_permission(identity, "read_files", record=record)
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
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        action = self.config.permission_action_prefix + "create_files"
        self.require_permission(identity, action, record=record)
        # TODO: Load via marshmallow schema?
        results = []
        for file_metadata in data:
            temporary_obj = deepcopy(file_metadata)
            results.append(
                record.files.create(
                    temporary_obj.pop('key'), data=temporary_obj))
        # TODO: maybe do this automatically in the files field
        db.session.commit()
        return self.file_result_list(
            self,
            identity,
            results=results,
            record=record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    def update_files_options(self, id_, identity, data):
        """Update the files' options."""
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        action = self.config.permission_action_prefix + "update_files"
        self.require_permission(identity, action, record=record)

        if record.files.enabled:
            if 'default_preview' in data:
                record.files.default_preview = data['default_preview']
            if 'order' in data:
                record.files.order = data['order']

        record.commit()
        db.session.commit()
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
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        self.require_permission(identity, "create", record=record)
        rf = record.files.update(file_key, data=data)
        db.session.commit()
        return self.file_result_item(
            self,
            identity,
            rf,
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def read_file_metadata(self, id_, file_key, identity):
        """Read the metadata of a file."""
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        self.require_permission(identity, "read_files", record=record)
        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    # TODO: `commit_file` might vary based on your storage backend (e.g. S3)
    def commit_file(self, id_, file_key, identity):
        """Commit a file upload."""
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        action = self.config.permission_action_prefix + "create_files"
        self.require_permission(identity, action, record=record)
        file_obj = ObjectVersion.get(record.bucket.id, file_key)
        if not file_obj:
            raise Exception(f'File with key {file_key} not uploaded yet.')
        # TODO: Add other checks here (e.g. verify checksum, S3 upload)
        record.files[file_key] = file_obj
        db.session.commit()
        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def delete_file(self, id_, file_key, identity):
        """Delete a single file."""
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        action = self.config.permission_action_prefix + "delete_files"
        self.require_permission(identity, action, record=record)
        deleted_file = record.files.delete(file_key)
        # We also commit the record in case the file was the `default_preview`
        record.commit()
        db.session.commit()
        return self.file_result_item(
            self,
            identity,
            deleted_file,
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def delete_all_files(self, id_, identity):
        """Delete all the files of the record."""
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        action = self.config.permission_action_prefix + "delete_files"
        self.require_permission(identity, action, record=record)
        # NOTE: We have to separate the gathering of the keys from their
        #       deletion because of how record.files is implemented.
        file_keys = [fk for fk in record.files]
        results = [record.files.delete(file_key) for file_key in file_keys]
        record.commit()
        return self.file_result_list(
            self,
            identity,
            results,
            record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    def set_file_content(
            self, id_, file_key, identity, stream,
            content_length=None):
        """Save file content."""
        # TODO stream not exhausted
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        action = self.config.permission_action_prefix + "create_files"
        self.require_permission(identity, action, record=record)
        rf = record.files.get(file_key)

        # TODO: raise an appropriate exception
        if rf is None:
            raise Exception(
                f'File with key "{file_key}" has not been initialized yet.')
        if rf.file:
            raise Exception(f'File with key "{file_key}" is commited.')

        bucket = record.bucket
        size_limit = bucket.size_limit
        if content_length and size_limit and content_length > size_limit:
            desc = 'File size limit exceeded.' \
                if isinstance(size_limit, int) else size_limit.reason
            raise FileSizeError(description=desc)
        # DB connection?
        # re uploading failed upload?

        with db.session.begin_nested():
            # TODO: in case we want to update a file, this keeps the old
            # FileInstance. It might be better to call ObjectVersion.remove()
            # before or after the "set_content"
            obj = ObjectVersion.create(bucket, file_key)
            obj.set_contents(
                stream, size=content_length, size_limit=size_limit)
        db.session.commit()
        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def get_file_content(self, id_, file_key, identity):
        """Retrieve file content."""
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)
        self.require_permission(identity, "read_files", record=record)
        # TODO Signal here or in resource?
        # file_downloaded.send(file_obj)
        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )
