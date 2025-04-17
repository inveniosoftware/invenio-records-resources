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
    EndpointLink,
    ExternalLink,
    Link,
    LinksTemplate,
    NestedLinks,
    Service,
    ServiceConfig,
)
from .files import FileLink, FileService, FileServiceConfig
from .records import (
    RecordEndpointLink,
    RecordIndexerMixin,
    RecordLink,
    RecordService,
    RecordServiceConfig,
    SearchOptions,
    ServiceSchemaWrapper,
    pagination_endpoint_links,
    pagination_links,
)

__all__ = (
    "ConditionalLink",
    "EndpointLink",
    "ExternalLink",
    "FileLink",
    "FileService",
    "FileServiceConfig",
    "Link",
    "LinksTemplate",
    "pagination_endpoint_links",
    "pagination_links",
    "RecordEndpointLink",
    "RecordLink",
    "RecordService",
    "RecordServiceConfig",
    "SearchOptions",
    "Service",
    "ServiceConfig",
    "ServiceSchemaWrapper",
    "RecordIndexerMixin",
    "NestedLinks",
)
