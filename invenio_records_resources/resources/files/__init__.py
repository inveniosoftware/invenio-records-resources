# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-License-Identifier: MIT

"""Invenio Resources module to create REST APIs."""

from .config import FileResourceConfig
from .resource import FileResource

__all__ = (
    "FileResourceConfig",
    "FileResource",
)
