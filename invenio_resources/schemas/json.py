# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Marshmallow JSON schema."""

from flask import current_app
from invenio_rest.serializer import BaseSchema as Schema
from marshmallow import (INCLUDE, ValidationError, fields, missing, post_load,
                         validates_schema)

from .fields import PersistentIdentifier


class OriginalKeysMixin(Schema):
    """Ensure all original keys are preserved on deserialization."""

    @post_load(pass_original=True)
    def load_unknown_fields(self, data, original_data):
        """Check for unknown keys."""
        if isinstance(original_data, list):
            for elem in original_data:
                self.load_unknown_fields(data, elem)
        else:
            for key, value in original_data.items():
                if key not in data:
                    data[key] = value
        return data


class RecordSchemaJSONV1(Schema):
    """Schema for records v1 in JSON."""

    # TODO: Remove this comment
    # attribute="pid.pid_value" is not needed anymore since it is always `id`
    # PID resolving happends only at controller level.
    id = fields.String(attribute="pid.pid_value")
    metadata = fields.Raw()
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


class RecordMetadataSchemaJSONV1(Schema):
    """Schema for records metadata v1 in JSON with injected PID value."""

    class Meta:
        """Meta attributes for the schema."""

        unknown = INCLUDE

    pid = PersistentIdentifier()

    def get_pid_field(self):
        """Return pid_field value."""
        return current_app.config["PIDSTORE_RECID_FIELD"]

    @post_load()
    def inject_pid(self, data, **kwargs):
        """Inject context PID in the RECID field."""
        # Remove already deserialized "pid" field
        pid_value = data.pop("pid", None)
        if pid_value:
            pid_field = self.get_pid_field()
            data.setdefault(pid_field, pid_value)
        return data
