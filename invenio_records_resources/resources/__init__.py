# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from .record import RecordResource
from .record_config import RecordResourceConfig
from .schema import RecordLinksSchema, SearchLinksSchema, search_link_params

__all__ = (
    "RecordResource",
    "RecordResourceConfig",
    "RecordLinksSchema",
    "SearchLinksSchema",
    "search_link_params"
)
