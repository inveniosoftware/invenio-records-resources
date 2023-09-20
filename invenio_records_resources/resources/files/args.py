# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Schemas for parameter parsing."""

from flask_resources.parsers import MultiDictSchema
from marshmallow import Schema, fields


class RequestExtraArgsSchema(MultiDictSchema):
    """Schema for request extra args."""

    include_deleted = fields.Bool()
