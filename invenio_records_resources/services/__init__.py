# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""High-level API for wokring with records, files, pids and search."""

from .base import (
    ConditionalLink,
    Link,
    Link2,
    LinksTemplate,
    NestedLinks,
    Service,
    ServiceConfig,
)
from .files import FileLink, FileService, FileServiceConfig
from .records import (
    RecordIndexerMixin,
    RecordLink,
    RecordLink2,
    RecordService,
    RecordServiceConfig,
    SearchOptions,
    ServiceSchemaWrapper,
    pagination_links,
    pagination_links2,
)

__all__ = (
    "ConditionalLink",
    "FileLink",
    "FileService",
    "FileServiceConfig",
    "Link",
    "Link2",
    "LinksTemplate",
    "pagination_links",
    "pagination_links2",
    "RecordLink",
    "RecordLink2",
    "RecordService",
    "RecordServiceConfig",
    "SearchOptions",
    "Service",
    "ServiceConfig",
    "ServiceSchemaWrapper",
    "RecordIndexerMixin",
    "NestedLinks",
)
