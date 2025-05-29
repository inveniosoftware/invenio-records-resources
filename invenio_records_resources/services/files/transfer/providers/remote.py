# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Remote file transfer provider."""

from urllib.parse import urlparse

from flask import current_app
from invenio_files_rest.models import FileInstance, ObjectVersion
from marshmallow import ValidationError, fields, validate, validates

from ...schema import BaseTransferSchema
from ..base import Transfer, TransferStatus
from ..constants import REMOTE_TRANSFER_TYPE


class RemoteTransferBase(Transfer):
    """Remote transfer base class."""

    class Schema(BaseTransferSchema):
        """Schema for remote transfer."""

        url = fields.Str(required=True, load_only=True)
        """URL that points to the remote file.
        
        It is not dumped to the client as it would make download statistics impossible.
        The file is accessed by using the /content url and then a 302 redirect 
        is sent to the client with the actual URI.
        """

        @validates("url")
        def validate_names(self, value):
            """Validate the domain of the URL is allowed."""
            # checking if storage class and uri are compatible is a
            # business logic concern, not a schema concern.
            if value:
                validate.URL(error="Not a valid URL.")(value)
                domain = urlparse(value).netloc
                allowed_domains = current_app.config.get(
                    "RECORDS_RESOURCES_FILES_ALLOWED_REMOTE_DOMAINS", ()
                )
                if domain not in allowed_domains:
                    raise ValidationError("Domain not allowed", field_name="url")


class RemoteTransfer(RemoteTransferBase):
    """Remote transfer."""

    transfer_type = REMOTE_TRANSFER_TYPE

    @property
    def status(self):
        """Get the status of the transfer."""
        # always return completed for remote files
        return TransferStatus.COMPLETED

    def send_file(self, *, as_attachment, **kwargs):
        """Send the file to the client."""
        return current_app.response_class(
            status=302,
            headers={
                "Location": self.file_record.transfer["url"],
            },
        )

    def init_file(self, record, file_metadata, **kwargs):
        """Initialize a file and return a file record."""
        url = file_metadata["transfer"]["url"]
        # all remote file records with the same URL share the same FileInstance
        fi = FileInstance.get_by_uri(url)
        if fi is None:
            fi = FileInstance.create()
            fi.set_uri(
                uri=file_metadata.get("transfer", {}).get("url"),
                size=file_metadata.get("size"),
                checksum=file_metadata.get("checksum"),
                readable=False,
            )
        obj = ObjectVersion.create(record.files.bucket, file_metadata["key"], fi.id)
        return super().init_file(record, file_metadata, obj=obj)
