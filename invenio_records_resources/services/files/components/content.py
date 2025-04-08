# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files service components."""

from ....proxies import current_transfer_registry
from ...errors import FailedFileUploadException, TransferException
from .base import FileServiceComponent


class FileContentComponent(FileServiceComponent):
    """File metadata service component."""

    def set_file_content(self, identity, id, file_key, stream, content_length, record):
        """Set file content handler."""
        # Check if associated file record exists and is not already committed.
        # TODO: raise an appropriate exception
        file_record = record.files.get(file_key)
        if file_record is None:
            raise Exception(f'File with key "{file_key}" has not been initialized yet.')

        transfer = current_transfer_registry.get_transfer(
            record=record,
            file_record=file_record,
            file_service=self.service,
            uow=self.uow,
        )
        try:
            transfer.set_file_content(stream, content_length)
        except TransferException:
            failed = record.files.delete(file_key, softdelete_obj=False, remove_rf=True)
            raise FailedFileUploadException(
                file_key=file_key, recid=record.pid, file=failed
            )

    def get_file_content(self, identity, id, file_key, record):
        """Get file content handler."""
        # TODO Signal here or in resource?
        # file_downloaded.send(file_obj)

    def delete_file(self, identity, id_, file_key, record, deleted_file):
        """Delete file handler."""
        transfer = current_transfer_registry.get_transfer(
            record=record,
            file_record=deleted_file,
            file_service=self.service,
            uow=self.uow,
        )
        transfer.delete_file()
