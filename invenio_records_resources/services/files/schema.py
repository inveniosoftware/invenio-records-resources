# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File schema."""

from marshmallow import EXCLUDE, Schema
from marshmallow.fields import UUID, Dict, Number, Str
from marshmallow_utils.fields import GenMethod, Links, SanitizedUnicode


class FileSchema(Schema):
    """Schema for records v1 in JSON."""

    class Meta:
        """Meta class to reject unknown fields."""

        unknown = EXCLUDE

    key = SanitizedUnicode(dump_only=True)
    created = Str(dump_only=True)
    updated = Str(dump_only=True)

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


class FilesLinks(Schema):
    """Search links schema."""

    links = Links()
