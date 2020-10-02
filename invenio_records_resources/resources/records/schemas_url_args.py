# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Schemas for parameter parsing."""


from marshmallow import Schema, fields, validate


class SearchURLArgsSchema(Schema):
    """Schema for search URL args."""

    q = fields.String()
    sort = fields.String()
    page = fields.Int(validate=validate.Range(min=1))
    size = fields.Int(validate=validate.Range(min=1))
