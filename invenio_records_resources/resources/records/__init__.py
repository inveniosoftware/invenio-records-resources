# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-License-Identifier: MIT

"""Invenio Resources module to create REST APIs."""

from .args import SearchRequestArgsSchema
from .config import RecordResourceConfig
from .resource import RecordResource

__all__ = (
    "RecordResource",
    "RecordResourceConfig",
    "SearchRequestArgsSchema",
)
