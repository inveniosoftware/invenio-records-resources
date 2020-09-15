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

from ...config import lt_es7
from ..base import Service
from .config import RecordServiceConfig
from .schema import MarshmallowServiceSchema
from ...linker.base import LinkStore


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
    def indexer(self):
        """Factory for creating an indexer instance."""
        return self.config.indexer_cls(record_cls=self.config.record_cls)

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
    def schema(self):
        """Returns the data schema instance."""
        return MarshmallowServiceSchema(schema=self.config.schema)

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
        pid, record = self.resolver.resolve(id_)
        # TODO: Fix me - this should be part of meta class for system fields.
        if not hasattr(record, '_obj_cache'):
            record._obj_cache = {}
        record._obj_cache['pid'] = pid
        return record

    #
    # High-level API
    #
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
            # Load record from ES dump.
            record = self.record_cls.loads(hit.to_dict()['_source'])

            links = LinkStore()
            record_projection = self.schema.dump(
                identity, record, pid=record.pid, record=record,
                links_store=links)
            item = self.result_item(
                record=record_projection, pid=record.pid, links=links)
            record_list.append(item)

        total = (
            search_result.hits.total
            if lt_es7
            else search_result.hits.total["value"]
        )

        aggregations = search_result.aggregations.to_dict()

        search_args = dict(q=querystring, **pagination, **sorting)
        # links = self.linker.links(
        #     "record_search", identity, search_args=search_args
        # )
        links = {}

        return self.result_list(
            record_list, total, aggregations, links
        )

    def create(self, identity, data):
        """Create a record.

        :param identity: Identity of user creating the record.
        :param data: Input data according to the data schema.
        """
        self.require_permission(identity, "create")

        # Validate data and create record with pid
        data, _ = self.schema.load(identity, data)
        record = self.record_cls.create({})

        # Run components
        for component in self.components:
            if hasattr(component, 'create'):
                component.create(identity, data=data, record=record)

        # Persist record (DB and index)
        record.commit()
        db.session.commit()
        if self.indexer:
            self.indexer.index(record)

        # Create record state
        # TODO (Alex): see how to replace resource unit
        links = LinkStore()
        record_projection = self.schema.dump(
            identity, record, pid=record.pid, record=record, links_store=links)
        return self.result_item(
            pid=record.pid, record=record_projection, links=links)

    def read(self, identity, id_):
        """Retrieve a record."""
        # Resolve and require permission
        # TODO must handle delete records and tombstone pages
        record = self.resolve(id_)
        self.require_permission(identity, "read", record=record)

        # Run components
        for component in self.components:
            if hasattr(component, 'read'):
                component.read(identity, record=record)

        # TODO: why record twice?
        links = LinkStore()
        record_projection = self.schema.dump(
            identity,
            record,
            # Schema context:
            pid=record.pid,
            record=record,
            links_store=links,
        )
        # TODO: how do we deal with tombstone pages
        return self.result_item(
            pid=record.pid, record=record_projection, links=links)

    def update(self, identity, id_, data):
        """Replace a record."""
        # TODO: etag and versioning
        record = self.resolve(id_)

        # Permissions
        self.require_permission(identity, "update", record=record)
        data, _ = self.schema.load(
            identity, data, pid=record.pid, record=record)

        # Run components
        for component in self.components:
            if hasattr(component, 'update'):
                component.update(identity, data=data, record=record)

        # TODO: remove next two lines.
        record.update(data)
        record.clear_none()
        record.commit()
        db.session.commit()

        if self.indexer:
            self.indexer.index(record)

        links = LinkStore()
        record_projection = self.schema.dump(
            identity, record, pid=record.pid, record=record, links_store=links)
        return self.result_item(
            pid=record.pid, record=record_projection, links=links)

    def delete(self, identity, id_):
        """Delete a record from database and search indexes."""
        # TODO: etag and versioning

        # TODO: Removed based on id both DB and ES
        record = self.resolve(id_)
        # Permissions
        self.require_permission(identity, "delete", record=record)

        # Run components
        for component in self.components:
            if hasattr(component, 'delete'):
                component.delete(identity, record=record)

        record.delete()
        record.pid.delete()
        db.session.commit()

        if self.indexer:
            self.indexer.delete(record)

        return True

        # TODO: Shall it return true/false? The tombstone page?
