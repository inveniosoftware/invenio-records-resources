# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from copy import deepcopy

from flask_babelex import gettext as _
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from invenio_records_permissions.policies.records import RecordPermissionPolicy
from invenio_search import RecordsSearch

from ..config import lt_es7
from ..links import Linker, RecordDeleteLinkBuilder, RecordFilesLinkBuilder, \
    RecordSearchLinkBuilder, RecordSelfLinkBuilder
from ..resource_units import IdentifiedRecord, IdentifiedRecords
from ..resources.record_config import RecordResourceConfig
from .data_validator import MarshmallowDataValidator
from .search import SearchEngine
from .search.serializers import es_to_record
from .service import Service, ServiceConfig


class RecordServiceConfig(ServiceConfig):
    """Service factory configuration."""

    # Common configuration
    permission_policy_cls = RecordPermissionPolicy
    resource_unit_cls = IdentifiedRecord
    resource_list_cls = IdentifiedRecords

    # Record specific configuration
    record_cls = Record
    resolver_cls = Resolver
    resolver_obj_type = "rec"
    resolver_pid_type = "recid"  # PID type for resolver and fetch
    minter_pid_type = "recid_v2"
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
    search_faceting_options = {}  # Concrete Records override this

    # Q: Do we want to keep same pattern as above and just pass classes?
    data_validator = MarshmallowDataValidator()

    # NOTE: Configuring routes here, allows their configuration and the
    #       configured routes to be picked up by the link builders at runtime
    record_route = RecordResourceConfig.item_route
    record_search_route = RecordResourceConfig.list_route
    record_files_route = RecordResourceConfig.item_route + "/files"
    record_link_builders = [
        RecordSelfLinkBuilder,
        RecordDeleteLinkBuilder,
        RecordFilesLinkBuilder,
    ]
    record_search_link_builders = [
        RecordSearchLinkBuilder
    ]


class RecordService(Service):
    """Record Service."""

    default_config = RecordServiceConfig

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(RecordService, self).__init__(*args, **kwargs)
        self.linker = Linker({
            "record": [
                lb(self.config) for lb in self.config.record_link_builders
            ],
            "record_search": [
                lb(self.config) for lb in
                self.config.record_search_link_builders
            ]
        })

    #
    # Low-level API
    #
    @property
    def resolver(self):
        """Factory for creating a resolver instance."""
        return self.config.resolver_cls(
            pid_type=self.config.resolver_pid_type,
            getter=self.config.record_cls.get_record
        )

    @property
    def minter(self):
        """Returns the minter function."""
        return current_pidstore.minters[self.config.minter_pid_type]

    @property
    def fetcher(self):
        """Returns the fetcher function."""
        return current_pidstore.fetchers[self.config.resolver_pid_type]

    @property
    def indexer(self):
        """Factory for creating an indexer instance."""
        return self.config.indexer_cls()

    @property
    def search_engine(self):
        """Factory for creating a search instance."""
        # This might grow over time
        options = {
            "faceting": self.config.search_faceting_options,
            "sorting": self.config.search_sort_options
        }
        return self.config.search_engine_cls(
            self.config.search_cls,
            options=options
        )

    @property
    def data_validator(self):
        """Returns the data validator instance."""
        return self.config.data_validator  # Already an instance

    @property
    def record_cls(self):
        """Factory for creating a record class."""
        return self.config.record_cls

    def resolve(self, id_):
        """Resolve a persistent identifier to a record."""
        return self.resolver.resolve(id_)

    #
    # High-level API
    #
    def read(self, identity, id_):
        """Retrieve a record."""
        pid, record = self.resolve(id_)
        self.require_permission(identity, "read", record=record)
        links = self.linker.links(
            "record", identity, pid_value=pid.pid_value, record=record
        )
        # TODO: how do we deal with tombstone pages
        return self.resource_unit(pid=pid, record=record, links=links)

    def search(self, identity, querystring, pagination=None, sorting=None,
               faceting=None):
        """Search for records matching the querystring."""
        # Permissions
        self.require_permission(identity, "search")

        # Search args
        pagination = pagination or {}
        sorting = sorting or {}
        # Because faceting includes any url args not parsed, it can include
        # garbage. We filter the garbage out, so that later generated links are
        # clean.
        faceting = self.search_engine.filter_facets(faceting or {})

        # Take a snapshot of search args to be able to transform them back into
        # a url
        original_search_args = dict(
            querystring=querystring,
            pagination=pagination,
            sorting=sorting,
            faceting=faceting
        )

        # Prepare arguments to search_arguments
        sorting = deepcopy(sorting)
        sorting["has_q"] = True if querystring else False
        extras = {}
        if not lt_es7:
            extras["track_total_hits"] = True

        # Parse query and execute search
        query = self.search_engine.parse_query(querystring)
        search_result = self.search_engine.search_arguments(
            pagination=pagination,
            sorting=sorting,
            faceting=faceting,
            extras=extras
        ).execute_search(query)

        # Mutate search results into a list of record states
        record_list = []
        for hit in search_result["hits"]["hits"]:
            # hit is ES AttrDict
            record = es_to_record(hit.to_dict(), self.record_cls)
            pid = self.fetcher(data=record, record_uuid=None)
            links = self.linker.links(
                "record", identity, pid_value=pid.pid_value, record=record
            )
            record_list.append(
                self.resource_unit(record=record, pid=pid, links=links)
            )

        total = (
            search_result.hits.total
            if lt_es7
            else search_result.hits.total["value"]
        )

        aggregations = search_result.aggregations.to_dict()

        links = self.linker.links(
            "record_search", identity, search_args=original_search_args
        )

        return self.resource_list(
            record_list, total, aggregations, links
        )

    def create(self, identity, data):
        """Create a record."""
        self.require_permission(identity, "create")
        data = self.data_validator.validate(data)
        record = self.record_cls.create(data)  # Create record in DB
        pid = self.minter(record_uuid=record.id, data=record)   # Mint PID
        links = self.linker.links(
            "record", identity, pid_value=pid.pid_value, record=record
        )

        # Create record state
        record_state = self.resource_unit(pid=pid, record=record, links=links)
        db.session.commit()  # Persist DB
        # Index the record
        if self.indexer:
            self.indexer.index(record)

        return record_state

    def delete(self, identity, id_):
        """Delete a record from database and search indexes."""
        # TODO: etag and versioning

        # TODO: Removed based on id both DB and ES
        pid, record = self.resolve(id_)
        # Permissions
        self.require_permission(identity, "delete", record=record)

        record.delete()
        pid.delete()

        db.session.commit()

        if self.indexer:
            self.indexer.delete(record)

        # TODO: Shall it return true/false? The tombstone page?

    def update(self, identity, id_, data):
        """Replace a record."""
        # TODO: etag and versioning
        pid, record = self.resolve(id_)
        # Permissions
        self.require_permission(identity, "update", record=record)
        # TODO: Data validation

        record.clear()
        record.update(data)
        record.commit()
        db.session.commit()

        if self.indexer:
            self.indexer.index(record)

        links = self.linker.links(
            "record", identity, pid_value=pid.pid_value, record=record
        )

        return self.resource_unit(pid=pid, record=record, links=links)
