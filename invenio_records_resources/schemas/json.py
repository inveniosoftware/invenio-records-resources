# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Marshmallow JSON schema."""


from marshmallow import INCLUDE, Schema, fields, missing, validate

from .fields import PersistentIdentifier, SanitizedUnicode


class MetadataSchemaJSONV1(Schema):
    """Basic metadata schema class."""

    class Meta:
        """Meta class to accept unknwon fields."""

        unknown = INCLUDE

    title = SanitizedUnicode(required=True, validate=validate.Length(min=3))


class RecordSchemaJSONV1(Schema):
    """Schema for records v1 in JSON."""

    # TODO: Remove this comment
    # attribute="pid.pid_value" is not needed anymore since it is always `id`
    # PID resolving happends only at controller level.
    id = fields.String(attribute="pid.pid_value")
    metadata = fields.Nested(MetadataSchemaJSONV1)
    links = fields.Raw()
    created = fields.Str()
    updated = fields.Str()


class Nested(fields.Nested):
    """Custom Nested class to not recursively check errors.

    .. versionadded:: 1.2.0
    """

    def _validate_missing(self, value):
        if value is missing and getattr(self, "required", False):
            self.fail("required")
        return super(Nested, self)._validate_missing(value)
