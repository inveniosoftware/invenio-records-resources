# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record schema."""
from copy import deepcopy
from datetime import timezone

from marshmallow import Schema, ValidationError, fields, pre_load
from marshmallow_utils.fields import Links, TZDateTime

from invenio_records_resources.errors import validation_error_to_list_errors


#
# The default record schema
#
class BaseRecordSchema(Schema):
    """Schema for records v1 in JSON."""

    id = fields.Str()
    created = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)
    updated = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)
    links = Links(dump_only=True)
    revision_id = fields.Integer(dump_only=True)

    @pre_load
    def clean(self, input_data, **kwargs):
        """Removes dump_only fields.

        Why: We want to allow the output of a Schema dump, to be a valid input
             to a Schema load without causing strange issues.
        """
        data = deepcopy(input_data)
        for name, field in self.fields.items():
            if field.dump_only:
                data.pop(name, None)
        return data


class BaseGhostSchema(Schema):
    """Base ghost schema."""

    is_ghost = fields.Constant(True, dump_only=True)


class ServiceSchemaWrapper:
    """Schema wrapper that enhances load/dump of wrapped schema.

    It:
        - allows strict (raises errors) / lax (reports them) loading by schema
        - constructs the context for the schema
            * injects the field permission check in the context
    """

    def __init__(self, service, schema):
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
                self._permission_policy_cls(action, **context, **kwargs).allows(
                    identity
                )
            )

        context.setdefault("field_permission_check", _permission_check)

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
