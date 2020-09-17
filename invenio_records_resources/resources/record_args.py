# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Schemas for parameter parsing."""


from marshmallow import Schema, ValidationError, fields, post_load, validate, \
    validates_schema

from ..pagination import Pagination

DEFAULT_RESULTS_PER_PAGE = 25
DEFAULT_MAX_RESULTS = 10000


class SearchArgsSchema(Schema):
    """Schema for search URL args."""

    q = fields.String()
    sort = fields.String()
    page = fields.Int(validate=validate.Range(min=1), missing=1)
    size = fields.Int(
        validate=validate.Range(min=1, max=DEFAULT_MAX_RESULTS),
        missing=DEFAULT_RESULTS_PER_PAGE
    )
    # from_ = fields.Int(
    #     validate=validate.Range(min=1), load_from='from', dump_to='from')

    @validates_schema
    def validate_pagination(self, data, **kwargs):
        """Validate pagination args make sense."""
        # if "page" in data and "from" in data:
        #     raise ValidationError(
        #         "The query parameters 'from' and 'page' must not be used at "
        #         "the same time."
        #     )
        page = Pagination(data["size"], data["page"], DEFAULT_MAX_RESULTS)
        if not page.valid():
            raise ValidationError("Invalid pagination parameters.")

    @post_load
    def _max_results(self, data, **kwargs):
        """Inject from_idx and to_idx into data bc they are valid."""
        data["_max_results"] = DEFAULT_MAX_RESULTS
        return data
