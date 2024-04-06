# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files metadata component components."""

from copy import deepcopy

from flask_babel import gettext as _
from flask import current_app
from invenio_files_rest.errors import FileSizeError

from ...errors import FilesCountExceededException
from ..schema import InitFileSchema
from .base import FileServiceComponent
from ....proxies import current_transfer_registry


class FileMetadataComponent(FileServiceComponent):
    """File metadata service component."""

    def init_files(self, identity, id, record, data):
        """Init files handler."""
        schema = InitFileSchema(many=True)
        validated_data = schema.load(data)

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
            transfer_type = temporary_obj.pop("storage_class", None)

            transfer = current_transfer_registry.get_transfer(
                transfer_type=transfer_type,
                service=self.service,
                uow=self.uow)

            _ = transfer.init_file(record, temporary_obj)

    def update_file_metadata(self, identity, id, file_key, record, data):
        """Update file metadata handler."""
        # FIXME: move this call to a transfer call
        record.files.update(file_key, data=data)

    def commit_file(self, identity, id, file_key, record):
        """Commit file handler."""

        transfer = current_transfer_registry.get_transfer(
            record=record,
            file_record=record.files.get(file_key),
            service=self.service,
            uow=self.uow)

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
