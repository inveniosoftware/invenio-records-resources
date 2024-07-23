# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files metadata component components."""

from copy import deepcopy

import marshmallow as ma
from flask import current_app
from flask_babel import gettext as _
from invenio_files_rest.errors import FileSizeError

from ....proxies import current_transfer_registry
from ...errors import FilesCountExceededException
from ...uow import RecordCommitOp
from .base import FileServiceComponent


class FileMetadataComponent(FileServiceComponent):
    """File metadata service component."""

    def init_files(self, identity, id, record, data):
        """Init files handler."""

        validated_data = []
        if not isinstance(data, list):
            raise ma.ValidationError("Expected a list of files.")

        for idx, file_metadata in enumerate(data):
            transfer_type = file_metadata.get("transfer_type", None)

            schema_cls = self.get_transfer_type_schema(transfer_type)

            schema = schema_cls()

            try:
                validated_data.append(schema.load(file_metadata))
            except ma.ValidationError as e:
                # add index to the error
                raise ma.ValidationError(
                    e.messages_dict,
                    field_name=idx,
                    data=e.data,
                    valid_data=e.valid_data,
                    **e.kwargs,
                )

        # All brand-new drafts don't allow exceeding files limit (while added via rest API).
        # Old records that already had more files than limited can continue adding files.
        # In case files amount goes back to under limit, users lose the privilege of adding more files.
        resulting_files_count = record.files.count + len(validated_data)
        maxFiles = self.service.config.max_files_count

        if maxFiles and record.files.count <= maxFiles:
            if resulting_files_count > maxFiles:
                raise FilesCountExceededException(
                    max_files=maxFiles, resulting_files_count=resulting_files_count
                )

        for file_metadata in validated_data:
            temporary_obj = deepcopy(file_metadata)
            transfer_type = temporary_obj.pop("transfer_type", None)

            transfer = current_transfer_registry.get_transfer(
                transfer_type=transfer_type,
                record=record,
                service=self.service,
                uow=self.uow,
            )

            _ = transfer.init_file(record, temporary_obj)

    def get_transfer_type_schema(self, transfer_type):
        """
        Get the transfer type schema. If the transfer type is not provided, the default schema is returned.
        If the transfer type is provided, the schema is created dynamically as a union of the default schema
        and the transfer type schema.

        Implementation details:
        For performance reasons, the schema is cached in the service config under "_file_transfer_schemas" key.
        """
        schema_cls = self.service.file_schema.schema
        if not transfer_type:
            return schema_cls

        if not hasattr(self.service.config, "_file_transfer_schemas"):
            self.service.config._file_transfer_schemas = {}

        # have a look in the cache
        if transfer_type in self.service.config._file_transfer_schemas:
            return self.service.config._file_transfer_schemas[transfer_type]

        # not there, create a subclass and put to the cache
        transfer = current_transfer_registry.get_transfer(
            transfer_type=transfer_type,
        )
        if transfer.Schema:
            schema_cls = type(
                f"{schema_cls.__name__}Transfer{transfer_type}",
                (transfer.Schema, schema_cls),
                {},
            )
        self.service.config._file_transfer_schemas[transfer_type] = schema_cls
        return schema_cls

    def update_file_metadata(self, identity, id, file_key, record, data):
        """Update file metadata handler."""
        # FIXME: move this call to a transfer call
        schema = self.service.file_schema.schema(many=False)

        # 'key' is required in the schema, but might not be in the data
        if "key" not in data:
            data["key"] = file_key
        validated_data = schema.load(data)
        record.files.update(file_key, data=validated_data)

    def update_transfer_metadata(
        self, identity, id, file_key, record, transfer_metadata
    ):
        """Update file transfer metadata handler."""
        file = record.files[file_key]

        file.transfer.set(transfer_metadata)
        self.uow.register(RecordCommitOp(file))

    def commit_file(self, identity, id, file_key, record):
        """Commit file handler."""

        transfer = current_transfer_registry.get_transfer(
            record=record,
            file_record=record.files.get(file_key),
            service=self.service,
            uow=self.uow,
        )

        transfer.commit_file()

        f_obj = record.files.get(file_key)
        f_inst = getattr(f_obj, "file", None)
        file_size = getattr(f_inst, "size", None)
        if file_size == 0:
            allow_empty_files = current_app.config.get(
                "RECORDS_RESOURCES_ALLOW_EMPTY_FILES", True
            )
            if not allow_empty_files:
                raise FileSizeError(description=_("Empty files are not accepted."))
