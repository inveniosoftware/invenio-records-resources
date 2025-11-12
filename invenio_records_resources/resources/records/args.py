# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Schemas for parameter parsing."""

from flask_resources.parsers import MultiDictSchema
from marshmallow import ValidationError, fields, post_load, validate, validates


class SearchRequestArgsSchema(MultiDictSchema):
    """Request URL query string arguments."""

    q = fields.String()
    suggest = fields.String()
    sort = fields.String()
    page = fields.Int(validate=validate.Range(min=1))
    size = fields.Int(validate=validate.Range(min=1))

    max_page_size = None  # to be set in context by sub-classes

    @post_load(pass_original=True)
    def facets(self, data, original_data=None, **kwargs):
        """Collect all unknown values into a facets key."""
        data["facets"] = {}
        for k in set(original_data.keys()) - set(data.keys()):
            data["facets"][k] = original_data.getlist(k)
        return data

    @validates("size")
    def validate_max_page_size(self, value):
        """Validate maximum page size."""
        if self.max_page_size and value > self.max_page_size:
            raise ValidationError(
                f"Page size cannot be greater than {self.max_page_size}."
            )
