# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Data validation API."""

from marshmallow import INCLUDE, Schema, fields, post_dump, pre_load, validate


class FieldPermissionError(Exception):
    """Marshmaallow field permission error."""


class MetadataSchemaJSONV1(Schema):
    """Basic metadata schema class."""

    class Meta:
        """Meta class to accept unknwon fields."""

        unknown = INCLUDE

    title = fields.Str(required=True, validate=validate.Length(min=3))


class RecordSchemaV1(Schema):
    """Schema for records v1 in JSON."""

    id = fields.Str()
    metadata = fields.Nested(MetadataSchemaJSONV1)
    links = fields.Raw()
    created = fields.Str()
    updated = fields.Str()


class FieldPermissionsMixin:
    """Mixin for filtering field-level permissions in marshmallow schemas."""

    field_load_permissions = {}
    field_dump_permissions = {}
    default_load_action = None
    default_dump_action = None

    @pre_load
    def _permissions_filter_load(self, data, **kwargs):
        field_permission_check = self.context.get("field_permission_check")
        if field_permission_check:
            for k in self.field_load_permissions:
                if k in data:
                    action = self.field_load_permissions[k] or \
                        self.default_load_action
                    # TODO (Alex): Maybe cache?
                    if action and not field_permission_check(action):
                        raise FieldPermissionError(k)
        return data

    @post_dump
    def _permissions_filter_dump(self, data, **kwargs):
        field_permission_check = self.context.get("field_permission_check")
        # NOTE: we make a copy since we don't want to modify the data when
        # deleting keys
        # TODO (Alex): see if actually needed...
        # data = deepcopy(data)
        if field_permission_check:
            for k in self.field_dump_permissions:
                if k in data:
                    action = self.field_dump_permissions[k] or \
                        self.default_dump_action
                    if action and not field_permission_check(action):
                        del data[k]
        return data
