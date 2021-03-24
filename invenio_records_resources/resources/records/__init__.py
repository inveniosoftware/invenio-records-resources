# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from .args import SearchRequestArgsSchema
from .config import RecordResourceConfig
from .resource import RecordResource

__all__ = (
    "RecordResource",
    "RecordResourceConfig",
    "SearchRequestArgsSchema",
)
