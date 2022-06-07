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
from marshmallow import fields, post_load, validate


class SearchRequestArgsSchema(MultiDictSchema):
    """Request URL query string arguments."""

    q = fields.String()
    suggest = fields.String()
    sort = fields.String()
    page = fields.Int(validate=validate.Range(min=1))
    size = fields.Int(validate=validate.Range(min=1))

    @post_load(pass_original=True)
    def facets(self, data, original_data=None, **kwargs):
        """Collect all unknown values into a facets key."""
        data["facets"] = {}
        for k in set(original_data.keys()) - set(data.keys()):
            data["facets"][k] = original_data.getlist(k)
        return data
