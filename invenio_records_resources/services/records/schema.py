# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record schema."""

from marshmallow import INCLUDE, Schema, ValidationError, fields, pre_load, \
    validate
from marshmallow_utils.fields import Links

from invenio_records_resources.errors import validation_error_to_list_errors


#
# The default record schema
#
class MetadataSchema(Schema):
    """Basic metadata schema class."""

    class Meta:
        """Meta class to accept unknown fields."""

        unknown = INCLUDE

    title = fields.Str(required=True, validate=validate.Length(min=3))


class BaseRecordSchema(Schema):
    """Schema for records v1 in JSON."""

    id = fields.Str()
    created = fields.Str(dump_only=True)
    updated = fields.Str(dump_only=True)
    links = Links(dump_only=True)
    revision_id = fields.Integer(dump_only=True)

    @pre_load
    def clean(self, data, **kwargs):
        """Removes dump_only fields.

        Why: We want to allow the output of a Schema dump, to be a valid input
             to a Schema load without causing strange issues.
        """
        for name, field in self.fields.items():
            if field.dump_only:
                data.pop(name, None)
        return data


class RecordSchema(BaseRecordSchema):
    """Schema for records v1 in JSON."""

    metadata = fields.Nested(MetadataSchema)


class SearchLinks(Schema):
    """Search links schema."""

    links = Links()


class ServiceSchemaWrapper:
    """Schema wrapper that enhances load/dump of wrapped schema.

    It:
        - allows strict (raises errors) / lax (reports them) loading by schema
        - constructs the context for the schema
            * injects the field permission check in the context
    """

    def __init__(self, service, schema=RecordSchema):
        """Constructor."""
        self.schema = schema
        # TODO: Change constructor to accept a permission_policy_cls directly
        self._permission_policy_cls = service.config.permission_policy_cls

    def _build_context(self, base_context):
        context = {**base_context}
        default_identity = context["identity"]  # identity required in context

        def _permission_check(action, identity=default_identity, **kwargs):
            return (
                # TODO: See if context is necessary here
                self._permission_policy_cls(action, **context, **kwargs)
                .allows(identity)
            )
        context.setdefault('field_permission_check', _permission_check)

        return context

    def load(self, data, schema_args=None, context=None, raise_errors=True):
        """Load data with dynamic schema_args + context + raise or not."""
        schema_args = schema_args or {}
        base_context = context or {}
        context = self._build_context(base_context)

        try:
            valid_data = self.schema(context=context, **schema_args).load(data)
            errors = []
        except ValidationError as e:
            if raise_errors:
                raise
            valid_data = e.valid_data
            errors = validation_error_to_list_errors(e)

        return valid_data, errors

    def dump(self, data, schema_args=None, context=None):
        """Dump data using wrapped schema and dynamic schema_args + context."""
        schema_args = schema_args or {}
        base_context = context or {}
        context = self._build_context(base_context)
        return self.schema(context=context, **schema_args).dump(data)
