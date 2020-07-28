# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Marshmallow schemas for serialization."""

from .json import MetadataSchemaJSONV1, Nested, RecordSchemaJSONV1
from .url_args import SearchURLArgsSchemaV1

__all__ = (
    "MetadataSchemaJSONV1",
    "Nested",
    "RecordSchemaJSONV1",
    "SearchURLArgsSchemaV1"
)
