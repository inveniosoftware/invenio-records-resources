# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from invenio_i18n import gettext as _
from invenio_indexer.api import RecordIndexer
from invenio_records_permissions.policies.records import RecordPermissionPolicy
from invenio_search import RecordsSearchV2

from ...records import Record
from ..base import ServiceConfig
from .components import MetadataComponent
from .links import RecordLink, pagination_links
from .params import FacetsParam, PaginationParam, QueryParser, QueryStrParam, SortParam
from .results import RecordItem, RecordList


class SearchOptions:
    """Search options."""

    search_cls = RecordsSearchV2
    query_parser_cls = QueryParser
    suggest_parser_cls = None
    sort_default = "bestmatch"
    sort_default_no_query = "newest"
    sort_options = {
        "bestmatch": dict(
            title=_("Best match"),
            fields=["_score"],  # ES defaults to desc on `_score` field
        ),
        "newest": dict(
            title=_("Newest"),
            fields=["-created"],
        ),
        "oldest": dict(
            title=_("Oldest"),
            fields=["created"],
        ),
    }
    facets = {}
    pagination_options = {"default_results_per_page": 25, "default_max_results": 10000}
    params_interpreters_cls = [QueryStrParam, PaginationParam, SortParam, FacetsParam]


class RecordServiceConfig(ServiceConfig):
    """Service factory configuration."""

    # Common configuration
    service_id = "records"
    permission_policy_cls = RecordPermissionPolicy
    result_item_cls = RecordItem
    result_list_cls = RecordList

    # Record specific configuration
    record_cls = Record
    indexer_cls = RecordIndexer
    indexer_queue_name = service_id
    index_dumper = None  # use default dumper defined on record class
    # inverse relation mapping, stores which fields relate to which record type
    relations = {}

    # Search configuration
    search = SearchOptions

    # Service schema
    schema = None  # Needs to be defined on concrete record service config

    links_item = {
        "self": RecordLink("{+api}/records/{id}"),
    }

    links_search = pagination_links("{+api}/records{?args*}")

    # Service components
    components = [
        MetadataComponent,
    ]
