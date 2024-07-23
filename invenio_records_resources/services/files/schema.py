# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
# Copyright (C) 2020 European Union.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File schema."""
from datetime import timezone

from flask import current_app
from marshmallow import (
    INCLUDE,
    RAISE,
    Schema,
    post_dump,
)
from marshmallow.fields import UUID, Boolean, Dict, Integer, Nested, Str
from marshmallow_utils.fields import Links, TZDateTime

from ...proxies import current_transfer_registry
from .transfer.registry import TransferRegistry


class InitFileSchema(Schema):
    """Service (component) schema for file initialization.

    The UI only sends a key and the documentation only refers to a key.
    The tests though pass other fields.

    Option 1: Only key
    Pros: We limit what we support, we prevent instances from saving data
          that we will need to support.
    Cons: Change a few tests, disable PUT endpoint really

    Option 2: Allow extra fields
    Pros: Everything stays the same.
    Cons: The same is loose / not quite consistent.

    Given LTS, going for option 2 so that many changes are not introduced.
    But ideally option 1 seems better: we can add other fields when we do
    support third-party data hosting (and perhaps become FileSchema).
    """

    class Meta:
        """Meta."""

        unknown = INCLUDE

    key = Str(required=True)
    storage_class = Str(default="L")
    transfer_type = Str(load_default=lambda: TransferRegistry.DEFAULT_TRANSFER_TYPE)
    checksum = Str()
    size = Integer()


class FileAccessSchema(Schema):
    """Schema for file access."""

    class Meta:
        """Meta."""

        unknown = RAISE

    hidden = Boolean()


class FileAccessSchema(Schema):
    """Schema for file access."""

    class Meta:
        """Meta."""

        unknown = RAISE

    hidden = Boolean()


class FileSchema(InitFileSchema):
    """Service schema for files."""

    class Meta:
        """Meta."""

        unknown = RAISE

    created = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)
    updated = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)

    mimetype = Str(dump_only=True, attribute="file.mimetype")
    version_id = UUID(attribute="file.version_id", dump_only=True)
    file_id = UUID(attribute="file.file_id", dump_only=True)
    bucket_id = UUID(attribute="file.bucket_id", dump_only=True)

    metadata = Dict()
    access = Nested(FileAccessSchema)

    links = Links()

    # comes from transfer_data
    # status = Str()
    # uri = Str()

    @post_dump(pass_many=False, pass_original=True)
    def _dump_technical_metadata(self, data, original_data, **kwargs):
        """
        Enriches the dumped data with the transfer data.
        """
        if original_data.file and original_data.file.file:
            data["mimetype"] = original_data.file.mimetype
            data["checksum"] = original_data.file.file.checksum
            data["size"] = original_data.file.file.size

        return data

    @post_dump(pass_many=False, pass_original=True)
    def _dump_transfer_data(self, data, original_data, **kwargs):
        """
        Enriches the dumped data with the transfer data.
        """
        transfer = current_transfer_registry.get_transfer(
            file_record=original_data,
            service=self.context.get("service"),
            record=self.context.get("record"),
        )
        data |= transfer.transfer_data
        return data
