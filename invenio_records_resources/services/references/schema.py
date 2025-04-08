# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Schema for entity references."""

from marshmallow import Schema, ValidationError, fields, validates_schema


#
# Schema for entity references
#
class EntityReferenceBaseSchema(Schema):
    """Base schema for entity references, allowing only a single key.

    Example of an allowed value: ``{"user": 1}``.
    Example of a disallowed value: ``{"user": 1, "record": "abcd-1234"}``.
    """

    @validates_schema
    def there_can_be_only_one(self, data, **kwargs):
        """Only allow a single key."""
        if len(data) != 1:
            raise ValidationError("Entity references may only have one key")

    @classmethod
    def create_from_dict(cls, allowed_types, special_fields=None):
        """Create an entity reference schema based on the allowed ref types.

        Per default, a ``fields.String()`` field is registered for each of
        the type names in the ``allowed_types`` list.
        The field type can be customized by providing an entry in the
        ``special_fields`` dict, with the type name as key and the field type
        as value (e.g. ``{"user": fields.Integer()}``).
        """
        field_types = special_fields or {}
        for ref_type in allowed_types:
            # each type would be a String field per default
            field_types.setdefault(ref_type, fields.String())

        return cls.from_dict(
            {ref_type: field_types[ref_type] for ref_type in allowed_types}
        )
