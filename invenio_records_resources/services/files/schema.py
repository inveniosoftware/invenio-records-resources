# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2020 European Union.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File schema."""

from datetime import timezone
from urllib.parse import urlparse

from flask import current_app
from marshmallow import (
    INCLUDE,
    RAISE,
    Schema,
    ValidationError,
    pre_dump,
    validate,
    validates,
)
from marshmallow.fields import UUID, Dict, Integer, Str
from marshmallow_utils.fields import GenMethod, Links, SanitizedUnicode, TZDateTime

from .transfer import TransferType


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

    key = SanitizedUnicode(required=True)
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

    @pre_dump(pass_many=False)
    def fields_from_file_obj(self, data, **kwargs):
        """Fields coming from the FileInstance model."""
        # this cannot be implemented as fields.Method since those receive the already
        # dumped data. it could not be access to data.file.
        # using data_key and attribute from marshmallow did not work as expected.

        # data is a FileRecord instance, might not have a file yet.
        # data.file is a File wrapper object.
        if data.file:
            # mandatory fields
            data["storage_class"] = data.file.storage_class
            data["uri"] = data.file.uri

            # If Local -> remove uri as it contains internal file storage info
            if not TransferType(data["storage_class"]).is_serializable():
                data.pop("uri")

            # optional fields
            fields = ["checksum", "size"]
            for field in fields:
                value = getattr(data.file, field, None)
                if value:
                    data[field] = value

        return data


class FileSchema(InitFileSchema):
    """Service schema for files."""

    class Meta:
        """Meta."""

        unknown = RAISE

    created = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)
    updated = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)

    status = GenMethod("dump_status")
    metadata = Dict(dump_only=True)
    mimetype = Str(dump_only=True, attribute="file.mimetype")
    version_id = UUID(attribute="file.version_id")
    file_id = UUID(attribute="file.file_id")
    bucket_id = UUID(attribute="file.bucket_id")

    links = Links()

    def dump_status(self, obj):
        """Dump file status."""
        # due to time constraints the status check is done here
        # however, ideally this class should not need knowledge of
        # the TransferType class, it should be encapsulated at File
        # wrapper class or lower.
        has_file = obj.file is not None
        if has_file and TransferType(obj.file.storage_class).is_completed:
            return "completed"

        return "pending"
