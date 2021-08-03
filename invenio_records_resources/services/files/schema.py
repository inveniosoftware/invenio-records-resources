# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File schema."""

from datetime import timezone

from marshmallow import INCLUDE, Schema
from marshmallow.fields import UUID, Dict, Number, Str
from marshmallow_utils.fields import GenMethod, Links, SanitizedUnicode, \
    TZDateTime


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


class FileSchema(Schema):
    """Service schema for files."""

    key = SanitizedUnicode(dump_only=True)
    created = TZDateTime(timezone=timezone.utc, format='iso', dump_only=True)
    updated = TZDateTime(timezone=timezone.utc, format='iso', dump_only=True)

    status = GenMethod('dump_status')

    metadata = Dict(dump_only=True)

    checksum = Str(dump_only=True, attribute='file.checksum')
    storage_class = Str(dump_only=True, attribute='file.storage_class')
    mimetype = Str(dump_only=True, attribute='file.mimetype')
    size = Number(attribute='file.size')
    version_id = UUID(attribute='file.version_id')
    file_id = UUID(attribute='file.file_id')
    bucket_id = UUID(attribute='file.bucket_id')

    links = Links()

    def dump_status(self, obj):
        """Dump file status."""
        return 'completed' if obj.file else 'pending'
