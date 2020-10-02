# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Schemas for header parsing."""


from marshmallow import Schema, fields


class RequestHeadersSchema(Schema):
    """Schema for search URL args."""

    if_match = fields.Integer()
