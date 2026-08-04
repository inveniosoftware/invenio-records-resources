# SPDX-FileCopyrightText: 2020-2026 CERN.
# SPDX-FileCopyrightText: 2024-2026 Graz University of Technology.
# SPDX-FileCopyrightText: 2025 KTH Royal Institute of Technology.
# SPDX-FileCopyrightText: 2026 Northwestern University.
# SPDX-FileCopyrightText: 2026 TU Wien.
# SPDX-License-Identifier: MIT

"""Invenio Resources module to create REST APIs."""

from .ext import InvenioRecordsResources

__version__ = "11.0.2"

__all__ = ("__version__", "InvenioRecordsResources")
