# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""High-level API for wokring with records, files, pids and search."""


from .base import ConditionalLink, Link, LinksTemplate, Service, ServiceConfig
from .files import FileLink, FileService, FileServiceConfig
from .records import (
    RecordIndexerMixin,
    RecordLink,
    RecordService,
    RecordServiceConfig,
    SearchOptions,
    ServiceSchemaWrapper,
    pagination_links,
)

__all__ = (
    "ConditionalLink",
    "FileLink",
    "FileService",
    "FileServiceConfig",
    "Link",
    "LinksTemplate",
    "pagination_links",
    "RecordLink",
    "RecordService",
    "RecordServiceConfig",
    "SearchOptions",
    "Service",
    "ServiceConfig",
    "ServiceSchemaWrapper",
    "RecordIndexerMixin",
)
