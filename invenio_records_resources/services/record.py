# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from invenio_records_permissions.policies.records import RecordPermissionPolicy
from invenio_search import RecordsSearch

from ..config import lt_es7
from ..resource_units import IdentifiedRecord, RecordSearchState
from .data_validator import MarshmallowDataValidator
from .search import SearchEngine
from .search.serializers import es_to_record
from .service import Service, ServiceConfig


class RecordServiceConfig(ServiceConfig):
    """Service factory configuration."""

    # Common configuration
    permission_policy_cls = RecordPermissionPolicy
    resource_unit_cls = IdentifiedRecord
    resource_list_cls = RecordSearchState

    # Record specific configuration
    record_cls = Record
    resolver_cls = Resolver
    resolver_obj_type = "rec"
    resolver_pid_type = "recid"  # PID type for resolver and fetch
    minter_pid_type = "recid_v2"
    indexer_cls = RecordIndexer
    search_cls = RecordsSearch
    search_engine_cls = SearchEngine
    # Q: Do we want to keep same pattern as above and just pass classes?
    data_validator = MarshmallowDataValidator()


class RecordService(Service):
    """Record Service."""

    default_config = RecordServiceConfig

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
        return self.config.search_engine_cls(self.config.search_cls)

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
    def read(self, id_, identity):
        """Retrieve a record."""
        pid, record = self.resolve(id_)
        self.require_permission(identity, "read", record=record)
        # Todo: how do we deal with tombstone pages
        return self.resource_unit(pid=pid, record=record)

    def search(self, querystring, identity, pagination=None, *args, **kwargs):
        """Search for records matching the querystring."""
        # Permissions
        # TODO rename by search in invenio-records-permission
        self.require_permission(identity, "list")

        # Add search arguments
        extras = {}
        if not lt_es7:
            extras["track_total_hits"] = True

        # Parse query and execute search
        query = self.search_engine.parse_query(querystring)
        search_result = self.search_engine.search_arguments(
            pagination=pagination,
            extras=extras
        ).execute_search(query)

        # Mutate search results into a list of record states
        record_list = []
        for hit in search_result["hits"]["hits"]:
            # hit is ES AttrDict
            record = es_to_record(hit.to_dict(), self.record_cls)
            pid = self.fetcher(data=record, record_uuid=None)
            record_list.append(self.resource_unit(record=record, pid=pid))

        total = (
            search_result.hits.total
            if lt_es7
            else search_result.hits.total["value"]
        )

        aggregations = search_result.aggregations.to_dict()

        return self.resource_list(record_list, total, aggregations)

    def create(self, data, identity):
        """Create a record."""
        self.require_permission(identity, "create")
        self.data_validator.validate(data)
        record = self.record_cls.create(data)  # Create record in DB
        pid = self.minter(record_uuid=record.id, data=record)   # Mint PID
        # Create record state
        record_state = self.resource_unit(pid=pid, record=record)
        db.session.commit()  # Persist DB
        # Index the record
        if self.indexer:
            self.indexer.index(record)

        return record_state

    def delete(self, id_, identity):
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

    def update(self, id_, data, identity):
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

        return self.resource_unit(pid=pid, record=record)
