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
        return MarshmallowServiceSchema(self, schema=self.config.schema)

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
    def search(self, identity, querystring, pagination=None, sorting=None,
               links_config=None):
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

        return self.result_list(
            self,
            identity,
            search_result,
            links_config=links_config
        )

    def create(self, identity, data, links_config=None):
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

        return self.result_item(
            self,
            identity,
            record,
            links_config=links_config
        )

    def read(self, id_, identity, links_config=None):
        """Retrieve a record."""
        # Resolve and require permission
        # TODO must handle delete records and tombstone pages
        record = self.resolve(id_)
        self.require_permission(identity, "read", record=record)

        # Run components
        for component in self.components:
            if hasattr(component, 'read'):
                component.read(identity, record=record)

        return self.result_item(
            self,
            identity,
            record,
            links_config=links_config
        )

    def update(self, id_, identity, data, links_config=None):
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

        return self.result_item(
            self,
            identity,
            record,
            links_config=links_config
        )

    def delete(self, id_, identity):
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
