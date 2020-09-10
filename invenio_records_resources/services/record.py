# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from functools import partial

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
from .components import AccessComponent, FilesComponent, MetadataComponent, \
    PIDSComponent
from .data_schema import MarshmallowDataSchema
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

    data_schema = MarshmallowDataSchema()

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

    components = [
        MetadataComponent,
        PIDSComponent,
        AccessComponent,
        FilesComponent,
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
            "sorting": self.config.search_sort_options
        }
        return self.config.search_engine_cls(
            self.config.search_cls,
            options=options
        )

    @property
    def data_schema(self):
        """Returns the data schema instance."""
        return self.config.data_schema  # Already an instance

    @property
    def components(self):
        """Return initialized service components."""
        return (c(self) for c in self.config.components)

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

        # Run components
        for component in self.components:
            if hasattr(component, 'read'):
                component.read(identity, record=record)

        record_projection = self.data_schema.dump(
            identity, record, pid=pid, record=record)
        links = self.linker.links(
            "record", identity, pid_value=pid.pid_value,
            record=record_projection
        )

        # TODO: how do we deal with tombstone pages
        return self.resource_unit(
            pid=pid, record=record_projection, links=links)

    def search(self, identity, querystring, pagination=None, sorting=None):
        """Search for records matching the querystring."""
        # Permissions
        self.require_permission(identity, "search")

        # Pagination
        pagination = pagination or {}

        # Sorting
        sorting = sorting or {}
        sorting["has_q"] = True if querystring else False

        # Add search arguments
        extras = {}
        if not lt_es7:
            extras["track_total_hits"] = True

        # Parse query and execute search
        query = self.search_engine.parse_query(querystring)

        # Run components
        for component in self.components:
            if hasattr(component, 'search'):
                # TODO (Alex): also parse and pass request data here...this has
                # to happen in the resource-level though filters, facets, etc.
                query = component.search(
                    identity, query,
                    querystring=querystring,
                    pagination=pagination,
                    sorting=sorting,
                )

        search_result = self.search_engine.search_arguments(
            pagination=pagination,
            sorting=sorting,
            extras=extras
        ).execute_search(query)

        # Mutate search results into a list of record states
        record_list = []
        for hit in search_result["hits"]["hits"]:
            # hit is ES AttrDict
            # TODO: Replace with `self.record_cls.load(cls=ESLoader)`
            record = es_to_record(hit.to_dict(), self.record_cls)
            pid = self.fetcher(data=record, record_uuid=None)
            # TODO: Since `RecordJSONSerializer._process_record` expects a
            # proper record class, we can't just dump and pass a projection...
            # record_projection = self.data_schema.dump(
            #     identity, record, pid=pid, record=record)
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

        search_args = dict(q=querystring, **pagination, **sorting)
        links = self.linker.links(
            "record_search", identity, search_args=search_args
        )

        return self.resource_list(
            record_list, total, aggregations, links
        )

    def create(self, identity, data):
        """Create a record.

        :param identity: Identity of user creating the record.
        :param data: Input data according to the data schema.
        """
        self.require_permission(identity, "create")

        data, _ = self.data_schema.load(identity, data)
        record = self.record_cls.create(data)  # Create record in DB
        pid = self.minter(record_uuid=record.id, data=record)   # Mint PID

        # Run components
        for component in self.components:
            if hasattr(component, 'create'):
                component.create(identity, data=data, record=record)

        # Persist record (DB and index)
        db.session.commit()
        if self.indexer:
            self.indexer.index(record)

        # Create record state
        # TODO (Alex): see how to replace resource unit
        record_projection = self.data_schema.dump(
            identity, record, pid=pid, record=record)

        links = self.linker.links(
            "record", identity, pid_value=pid.pid_value,
            record=record_projection
        )

        return self.resource_unit(
            pid=pid, record=record_projection, links=links)

    def delete(self, identity, id_):
        """Delete a record from database and search indexes."""
        # TODO: etag and versioning

        # TODO: Removed based on id both DB and ES
        pid, record = self.resolve(id_)
        # Permissions
        self.require_permission(identity, "delete", record=record)

        # Run components
        for component in self.components:
            if hasattr(component, 'delete'):
                component.delete(identity, record=record)

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
        data, _ = self.data_schema.load(identity, data, pid=pid, record=record)

        # Run components
        for component in self.components:
            if hasattr(component, 'update'):
                component.update(identity, data=data, record=record)

        # TODO: Change once system fields and `Record.clean_none()` are there
        record.clear()
        record.update(data)
        record.commit()
        db.session.commit()

        if self.indexer:
            self.indexer.index(record)

        record_projection = self.data_schema.dump(
            identity, record, pid=pid, record=record)
        links = self.linker.links(
            "record", identity, pid_value=pid.pid_value,
            record=record_projection
        )

        return self.resource_unit(
            pid=pid, record=record_projection, links=links)
