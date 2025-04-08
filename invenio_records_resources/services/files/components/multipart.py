# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files service components."""

from werkzeug.exceptions import NotFound

from invenio_records_resources.proxies import current_transfer_registry
from invenio_records_resources.services.files.transfer.providers.multipart import (
    MultipartTransfer,
)

from ...errors import FailedFileUploadException, TransferException
from .base import FileServiceComponent


class FileMultipartContentComponent(FileServiceComponent):
    """File metadata service component."""

    def set_multipart_file_content(
        self, identity, id, file_key, part, stream, content_length, record
    ):
        """Set file content handler."""
        # Check if associated file record exists and is not already committed.
        file_record = record.files.get(file_key)

        if file_record is None:
            raise NotFound(f'File with key "{file_key}" has not been initialized yet.')

        transfer = current_transfer_registry.get_transfer(
            record=record,
            file_record=file_record,
            file_service=self.service,
            uow=self.uow,
        )
        if not isinstance(transfer, MultipartTransfer):
            raise TransferException(
                f'Transfer type "{transfer.transfer_type}" does not support multipart uploads.'
            )

        try:
            transfer.set_file_multipart_content(part, stream, content_length)
        except TransferException:
            raise FailedFileUploadException(
                file_key=file_key, recid=record.pid, file=file_record
            )
