# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from .config import FileActionResourceConfig, FileResourceConfig
from .resource import FileActionResource, FileResource

__all__ = (
    "FileActionResource",
    "FileActionResourceConfig",
    "FileResourceConfig",
    "FileResource",
)
