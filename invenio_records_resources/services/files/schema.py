# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2020 European Union.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File schema."""
import typing
from datetime import timezone
from urllib.parse import urlparse

from flask import current_app
from marshmallow import (
    INCLUDE,
    RAISE,
    Schema,
    ValidationError,
    pre_dump,
    post_dump,
    validate,
    validates,
)
from marshmallow.fields import UUID, Dict, Integer, Str
from marshmallow.schema import _T
from marshmallow.utils import missing
from marshmallow_utils.fields import GenMethod, Links, SanitizedUnicode, TZDateTime

from .transfer import BaseTransfer
from ...proxies import current_transfer_registry


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
    storage_class = Str()
    uri = Str()
    checksum = Str()
    size = Integer()

    @validates("uri")
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

    def dump(self, obj: typing.Any, *, many = None, **kwargs):
        raise Exception("InitFileSchema should not be used for dumping.")


class FileSchema(Schema):
    """Service schema for files."""

    class Meta:
        """Meta."""

        unknown = RAISE

    key = Str(required=True)

    created = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)
    updated = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)

    metadata = Dict(dump_only=True)
    mimetype = Str(dump_only=True, attribute="file.mimetype")
    checksum = Str(dump_only=True, attribute="file.checksum")
    size = Integer(dump_only=True, attribute="file.size")

    storage_class = Str(dump_only=True, attribute="file.storage_class")

    version_id = UUID(attribute="file.version_id")
    file_id = UUID(attribute="file.file_id")
    bucket_id = UUID(attribute="file.bucket_id")

    links = Links()

    # comes from transfer_data
    # status = Str()
    # uri = Str()

    @post_dump(pass_many=False, pass_original=True)
    def _dump_transfer_data(self, data, original_data, **kwargs):
        """
        Enriches the dumped data with the transfer data.
        """
        transfer = current_transfer_registry.get_transfer(file_record=original_data)
        data |= transfer.transfer_data
        return data
