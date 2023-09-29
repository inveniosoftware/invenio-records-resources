# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files service components."""
from ...errors import FailedFileUploadException, TransferException
from ..transfer import Transfer
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

        file_type = file_record.file.storage_class if file_record.file else None
        transfer = Transfer.get_transfer(file_type)
        try:
            transfer.set_file_content(
                record, file_record.file, file_key, stream, content_length
            )
        except TransferException as e:
            failed = record.files.delete(file_key, softdelete_obj=False, remove_rf=True)
            raise FailedFileUploadException(
                file_key=file_key, recid=record.pid, file=failed
            )

    def get_file_content(self, identity, id, file_key, record):
        """Get file content handler."""
        # TODO Signal here or in resource?
        # file_downloaded.send(file_obj)
