# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Mock module schemas."""

from marshmallow import Schema, fields, validate
from marshmallow.utils import get_value
from marshmallow_utils.fields import SanitizedUnicode

from invenio_records_resources.services.records.schema import BaseRecordSchema


class TypeSchema(Schema):
    """Nested type schema used for faceting tests."""

    type = fields.Str()
    subtype = fields.Str()


class ReferencedCreatedBySchema(Schema):
    """Nested type schema for fake created by field."""

    user = fields.Integer()
    entity = fields.Str()


class ReferencedNestedSchema(Schema):
    """Nested type schema for fake other.nested field."""

    sub = fields.Str()


class ReferencedOtherSchema(Schema):
    """Nested type schema for fake other field."""

    nested = fields.Nested(ReferencedNestedSchema)


class MetadataSchema(Schema):
    """Basic metadata schema class."""

    title = fields.Str(required=True, validate=validate.Length(min=3))
    type = fields.Nested(TypeSchema)
    subject = fields.Str()
    inner_record = fields.Dict()
    # referenced records
    referenced_created_by = fields.Nested(ReferencedCreatedBySchema)
    referenced_simple = fields.Str()
    referenced_simple_same = fields.Str()
    referenced_other = fields.Nested(ReferencedOtherSchema)


class RecordSchema(BaseRecordSchema):
    """Test RecordSchema."""

    metadata = fields.Nested(MetadataSchema)


class FilesOptionsSchema(Schema):
    """Basic files options schema class."""

    enabled = fields.Bool(missing=True)
    # allow unsetting
    default_preview = SanitizedUnicode(allow_none=True)

    def get_attribute(self, obj, attr, default):
        """Override how attributes are retrieved when dumping.

        NOTE: We have to access by attribute because although we are loading
              from an external pure dict, but we are dumping from a data-layer
              object whose fields should be accessed by attributes and not
              keys. Access by key runs into FilesManager key access protection
              and raises.
        """
        value = getattr(obj, attr, default)

        if attr == "default_preview" and not value:
            return default

        return value


class RecordWithFilesSchema(RecordSchema):
    """Schema for records with files."""

    files = fields.Nested(FilesOptionsSchema, required=True)

    def get_attribute(self, obj, attr, default):
        """Override how attributes are retrieved when dumping.

        NOTE: We have to access by attribute because although we are loading
              from an external pure dict, but we are dumping from a data-layer
              object whose fields should be accessed by attributes and not
              keys. Access by key runs into FilesManager key access protection
              and raises.
        """
        if attr == "files":
            return getattr(obj, attr, default)
        else:
            return get_value(obj, attr, default)
