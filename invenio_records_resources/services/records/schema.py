# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record schema."""

from invenio_records_rest.schemas.fields import GenFunction
from marshmallow import INCLUDE, Schema, ValidationError, fields, validate

from ...linker.base import LinksField
from ...schemas import FieldPermissionsMixin


#
# The default record schema
#
class RecordLinks(Schema, FieldPermissionsMixin):
    """Links schema."""

    field_dump_permissions = {
        'self': 'read',
    }

    self = GenFunction(lambda obj, ctx: {'pid_value': obj.pid.pid_value})


class MetadataSchema(Schema):
    """Basic metadata schema class."""

    class Meta:
        """Meta class to accept unknown fields."""

        unknown = INCLUDE

    title = fields.Str(required=True, validate=validate.Length(min=3))


class RecordSchema(Schema):
    """Schema for records v1 in JSON."""

    id = fields.Str()
    metadata = fields.Nested(MetadataSchema)
    links = LinksField(links_schema=RecordLinks, namespace='record')
    created = fields.Str()
    updated = fields.Str()


#
# Service schema implementation (adds e.g. permission filtering)
#
class ServiceSchema:
    """Data validator interface."""

    def __init__(self, service, *args, **kwargs):
        """Constructor."""
        self.service = service

    def load(self, identity, data, *args, **kwargs):
        """Load data."""
        raise NotImplementedError()

    def dump(self, identity, data, *args, **kwargs):
        """Dump data."""
        raise NotImplementedError()


class MarshmallowServiceSchema(ServiceSchema):
    """Data schema based on Marshmallow."""

    def __init__(self, service, *args, schema=RecordSchema, **kwargs):
        """Constructor."""
        self.schema = schema
        self._service = service
        super().__init__(self, *args, **kwargs)

    def _build_context(self, identity, **context):
        def _permission_check(action, identity=identity, **kwargs):
            return self._service.config.permission_policy_cls(
                action, **context, **kwargs).allows(identity)
        context.setdefault('field_permission_check', _permission_check)
        context.setdefault('identity', identity)
        return context

    def load(self, identity, data, raise_errors=True, schema_args=None,
             **kwargs):
        """Load data using the marshmallow schema."""
        schema_args = schema_args or {}
        context = self._build_context(identity, **kwargs)
        try:
            valid_data = self.schema(context=context, **schema_args).load(data)
            errors = None
        except ValidationError as e:
            if raise_errors:
                raise
            valid_data = e.valid_data
            errors = e.messages
        return valid_data, errors

    def dump(self, identity, data, schema_args=None, **kwargs):
        """Dump data using the marshmallow schema."""
        schema_args = schema_args or {}
        context = self._build_context(identity, **kwargs)
        return self.schema(context=context, **schema_args).dump(data)
