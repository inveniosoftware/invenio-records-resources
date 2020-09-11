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
from invenio_search import RecordsSearch

from ...config import lt_es7
from ...linker import DeleteLinkBuilder, FilesLinkBuilder, Linker, \
    SearchLinkBuilder, SelfLinkBuilder
from ...records import Record
from ...search import SearchEngine
from ..base import ServiceConfig
from .components import AccessComponent, FilesComponent, MetadataComponent, \
    PIDSComponent
from .results import IdentifiedRecord, IdentifiedRecords
from .schema import RecordSchema


class RecordServiceConfig(ServiceConfig):
    """Service factory configuration."""

    # Common configuration
    permission_policy_cls = RecordPermissionPolicy
    result_item_cls = IdentifiedRecord
    result_list_cls = IdentifiedRecords

    # Record specific configuration
    record_cls = Record
    resolver_cls = Resolver
    resolver_obj_type = "rec"
    resolver_pid_type = "recid"  # PID type for resolver and fetch

    indexer_cls = RecordIndexer

    search_cls = RecordsSearch
    search_engine_cls = SearchEngine
    search_sort_options = dict(
        bestmatch=dict(
            title=_('Best match'),
            fields=['-_score'],
            default_if_query=True,
        ),
        mostrecent=dict(
            title=_('Most recent'),
            fields=['-_created'],
            default_if_no_query=True,
        ),
    )

    schema = RecordSchema

    # NOTE: Configuring routes here, allows their configuration and the
    #       configured routes to be picked up by the link builders at runtime
    # record_route = RecordResourceConfig.item_route
    # record_search_route = RecordResourceConfig.list_route
    # record_files_route = RecordResourceConfig.item_route + "/files"

    components = [
        MetadataComponent,
        PIDSComponent,
        AccessComponent,
        FilesComponent,
    ]

    # TODO: Can they be moved outside?
    record_link_builders = [
        SelfLinkBuilder,
        DeleteLinkBuilder,
        FilesLinkBuilder,
    ]
    record_search_link_builders = [
        SearchLinkBuilder
    ]
