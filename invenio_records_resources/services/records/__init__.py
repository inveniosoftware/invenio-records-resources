# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-License-Identifier: MIT

"""Record Service API."""

from .config import RecordServiceConfig, SearchOptions
from .links import (
    RecordEndpointLink,
    RecordLink,
    pagination_endpoint_links,
    pagination_links,
)
from .schema import ServiceSchemaWrapper
from .service import RecordIndexerMixin, RecordService

__all__ = (
    "pagination_endpoint_links",
    "pagination_links",
    "RecordEndpointLink",
    "RecordLink",
    "RecordService",
    "RecordServiceConfig",
    "SearchOptions",
    "ServiceSchemaWrapper",
    "RecordIndexerMixin",
)
