# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2025 CERN.
# Copyright (C) 2024-2026 Graz University of Technology.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from .ext import InvenioRecordsResources

__version__ = "9.0.0"

__all__ = ("__version__", "InvenioRecordsResources")
