# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Files metadata component components."""

from flask import current_app
from flask_babel import gettext as _
from invenio_files_rest.errors import FileSizeError

from ....proxies import current_transfer_registry
from ...errors import FilesCountExceededException
from ...uow import RecordCommitOp
from .base import FileServiceComponent


class FileMetadataComponent(FileServiceComponent):
    """File metadata service component."""

    def init_files(self, identity, id_, record, data):
        """Init files handler."""
        # All brand-new drafts don't allow exceeding files limit (while added via rest API).
        # Old records that already had more files than limited can continue adding files.
        # In case files amount goes back to under limit, users lose the privilege of adding more files.
        resulting_files_count = record.files.count + len(data)
        maxFiles = self.service.config.max_files_count

        if maxFiles and record.files.count <= maxFiles:
            if resulting_files_count > maxFiles:
                raise FilesCountExceededException(
                    max_files=maxFiles, resulting_files_count=resulting_files_count
                )

        for file_metadata in data:
            transfer = current_transfer_registry.get_transfer(
                record=record,
                file_service=self.service,
                key=file_metadata["key"],
                transfer_type=file_metadata["transfer"]["type"],
                uow=self.uow,
            )

            _ = transfer.init_file(record, file_metadata)

    def update_file_metadata(self, identity, id_, file_key, record, data):
        """Update file metadata handler."""
        schema = self.service.file_schema.schema(many=False)
        validated_data = schema.load(data)
        record.files.update(file_key, data=validated_data)

    def update_transfer_metadata(
        self, identity, id, file_key, record, transfer_metadata
    ):
        """Update file transfer metadata handler."""
        file = record.files[file_key]

        file.transfer.set(transfer_metadata)
        self.uow.register(RecordCommitOp(file))

    def commit_file(self, identity, id_, file_key, record):
        """Commit file handler."""
        transfer = current_transfer_registry.get_transfer(
            record=record,
            file_record=record.files.get(file_key),
            file_service=self.service,
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
