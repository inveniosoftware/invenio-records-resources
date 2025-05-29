# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Fetch transfer provider."""

from urllib.parse import urlparse

from flask import current_app
from marshmallow import ValidationError, fields, validate, validates

from invenio_records_resources.services.files.transfer.base import TransferStatus

from ....uow import RecordCommitOp, TaskOp
from ...schema import BaseTransferSchema
from ...tasks import fetch_file
from ..constants import FETCH_TRANSFER_TYPE, LOCAL_TRANSFER_TYPE
from .remote import RemoteTransferBase


class FetchTransfer(RemoteTransferBase):
    """Fetch transfer.

    This transfer provider is used to fetch a file from a remote location. The external
    file will be downloaded and stored in the record's bucket. When this is done, the
    transfer type will be changed to `local` and the file will be available for download.
    """

    transfer_type = FETCH_TRANSFER_TYPE

    class Schema(BaseTransferSchema):
        """Schema for fetch transfer."""

        url = fields.Url(required=True, load_only=True)
        """URL to fetch the file from. 
        
        Note: the url is never dumped to the client as it can contain credentials (
        basic http authentication, pre-signed request, ...) and should not be exposed.
        """
        error = fields.Str(dump_only=True)

        @validates("url")
        def validate_names(self, value):
            """Validate the domain of the URI is allowed."""
            # checking if storage class and uri are compatible is a
            # business logic concern, not a schema concern.
            if value:
                validate.URL(error="Not a valid URL.")(value)
                domain = urlparse(value).netloc
                allowed_domains = current_app.config.get(
                    "RECORDS_RESOURCES_FILES_ALLOWED_DOMAINS"
                )
                if domain not in allowed_domains:
                    raise ValidationError("Domain not allowed", field_name="uri")

    def init_file(self, record, file_metadata, **kwargs):
        """Initialize a file and return a file record."""
        file = super().init_file(record, file_metadata, **kwargs)

        self.uow.register(
            TaskOp(
                fetch_file,
                service_id=self.file_service.id,
                record_id=record.pid.pid_value,
                file_key=file.key,
            )
        )
        return file

    def set_file_content(self, stream, content_length):
        """Set file content."""
        super().set_file_content(stream, content_length)

    def commit_file(self):
        """Commit the file."""
        super().commit_file()
        self.file_record.transfer.transfer_type = LOCAL_TRANSFER_TYPE
        self.uow.register(RecordCommitOp(self.file_record))

    @property
    def status(self):
        """Get the status of the transfer."""
        # always return completed for remote files
        if self.file_record.transfer.get("error"):
            return TransferStatus.FAILED
        return super().status
