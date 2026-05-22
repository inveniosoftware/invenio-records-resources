# SPDX-FileCopyrightText: 2020-2026 CERN.
# SPDX-FileCopyrightText: 2024-2026 Graz University of Technology.
# SPDX-FileCopyrightText: 2025 KTH Royal Institute of Technology.
# SPDX-FileCopyrightText: 2026 Northwestern University.
# SPDX-License-Identifier: MIT

"""Invenio Resources module to create REST APIs."""

from .ext import InvenioRecordsResources

__version__ = "10.1.0"

__all__ = ("__version__", "InvenioRecordsResources")
