# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from flask_babelex import gettext as _
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.resolver import Resolver
from invenio_records_permissions.policies.records import RecordPermissionPolicy
from invenio_search import RecordsSearchV2

from ...records import Record
from ..base import ServiceConfig
from .components import MetadataComponent
from .params import FacetsParam, PaginationParam, QueryParser, QueryStrParam, \
    SortParam
from .results import RecordItem, RecordList
from .schema import RecordSchema, SearchLinks


class RecordServiceConfig(ServiceConfig):
    """Service factory configuration."""

    # Common configuration
    permission_policy_cls = RecordPermissionPolicy
    result_item_cls = RecordItem
    result_list_cls = RecordList

    # Record specific configuration
    record_cls = Record
    indexer_cls = RecordIndexer
    index_dumper = None  # use default dumper defined on record class

    # # Search configuration
    search_cls = RecordsSearchV2
    search_query_parser_cls = QueryParser
    search_sort_default = 'bestmatch'
    search_sort_default_no_query = 'newest'
    search_sort_options = {
        "bestmatch": dict(
            title=_('Best match'),
            fields=['_score'],  # ES defaults to desc on `_score` field
        ),
        "newest": dict(
            title=_('Newest'),
            fields=['-created'],
        ),
        "oldest": dict(
            title=_('Oldest'),
            fields=['created'],
        ),
    }
    search_facets_options = dict(
        aggs={},
        post_filters={}
    )
    search_pagination_options = {
        "default_results_per_page": 25,
        "default_max_results": 10000
    }
    search_params_interpreters_cls = [
        QueryStrParam,
        PaginationParam,
        SortParam,
        FacetsParam
    ]

    schema = RecordSchema
    schema_search_links = SearchLinks

    components = [
        MetadataComponent,
    ]
