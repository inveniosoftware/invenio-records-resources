# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2021-2025 CERN.
# Copyright (C) 2021-2023 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Mock module schemas."""

from marshmallow import Schema, fields, missing, validate
from marshmallow.utils import get_value
from marshmallow_utils.fields import SanitizedUnicode

from invenio_records_resources.services.errors import ValidationErrorGroup
from invenio_records_resources.services.records.schema import BaseRecordSchema


class TypeSchema(Schema):
    """Nested type schema used for faceting tests."""

    type = fields.Str()
    subtype = fields.Str()


class SubjectSchema(Schema):
    """Nested subject schema used for faceting tests."""

    scheme = fields.Str()
    subject = fields.Str()


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
    subjects = fields.List(fields.Nested(SubjectSchema))
    combined_subjects = fields.List(fields.Str)
    inner_record = fields.Dict()
    # referenced records
    referenced_created_by = fields.Nested(ReferencedCreatedBySchema)
    referenced_simple = fields.Str()
    referenced_simple_same = fields.Str()
    referenced_other = fields.Nested(ReferencedOtherSchema)

    # test field for triggering a ValidationErrorGroup exception
    trigger_error_group = fields.Method(deserialize="load_trigger_error_group")

    def load_trigger_error_group(self, value):
        """Load trigger error group."""
        if not value:
            return missing
        # NOTE: This is not meant to be in any way the proper way to return multiple
        # validation errors in a marshmallow schema (use `marshmallow.ValidationError`
        # instead). This is here because it's a convenient way to hook-in and raise an
        # exception in tests.
        raise ValidationErrorGroup(
            errors=[
                {
                    "field": "metadata.trigger_error_group",
                    "messages": ["Error 1 in error group", "Error 2 in error group"],
                },
                {
                    "field": "metadata.title",
                    "messages": ["Test warning for title field error group."],
                    "description": "Test description for title field error group.",
                    "severity": "warning",
                },
            ]
        )


class RecordSchema(BaseRecordSchema):
    """Test RecordSchema."""

    metadata = fields.Nested(MetadataSchema)


class FilesSchema(Schema):
    """Basic files schema class."""

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

    files = fields.Nested(FilesSchema, required=True)

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
