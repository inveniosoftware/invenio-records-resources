# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2023 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from .ext import InvenioRecordsResources

__version__ = "1.1.0"

__all__ = ("__version__", "InvenioRecordsResources")
