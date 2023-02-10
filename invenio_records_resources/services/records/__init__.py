# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from .config import RecordServiceConfig, SearchOptions
from .links import RecordLink, pagination_links
from .schema import ServiceSchemaWrapper
from .service import RecordIndexerMixin, RecordService

__all__ = (
    "pagination_links",
    "RecordLink",
    "RecordService",
    "RecordServiceConfig",
    "SearchOptions",
    "ServiceSchemaWrapper",
    "RecordIndexerMixin",
)
