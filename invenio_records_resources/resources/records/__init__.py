# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from .config import RecordResourceConfig
from .errors import create_pid_redirected_error_handler
from .resource import RecordResource
from .response import RecordResponse
from .schemas_header import RequestHeadersSchema
from .schemas_links import ItemLink, ItemLinksSchema, LinksSchema, \
    SearchLink, SearchLinksSchema, search_link_params, search_link_when
from .schemas_url_args import SearchURLArgsSchema

__all__ = (
    "create_pid_redirected_error_handler",
    "ItemLink",
    "ItemLinksSchema",
    "LinksSchema",
    "RecordResource",
    "RecordResourceConfig",
    "RecordResponse",
    "RequestHeadersSchema",
    "search_link_params",
    "search_link_when",
    "SearchLink",
    "SearchLinksSchema",
    "SearchURLArgsSchema",
)
