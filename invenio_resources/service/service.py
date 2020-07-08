# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Agent is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Agent API."""

from flask_principal import Permission
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from invenio_search import RecordsSearch

from ..config import lt_es7
from .errors import PermissionDeniedError
from .search import SearchEngine
from .search.serializers import es_to_record
from .state import RecordSearchState, RecordState


class RecordServiceConfig:
    """Service factory configuration."""

    record_cls = Record
    resolver_cls = Resolver
    resolver_obj_type = "rec"
    pid_type = "recid"  # PID type for resolver, minter, and fetcher
    permission_policy_cls = ""
    record_state_cls = RecordState
    # Class dependency injection
    indexer_cls = RecordIndexer
    search_cls = RecordsSearch
    search_engine_cls = SearchEngine

    # pid = 'recidv2'
    # pids = ['doi', ]

    #
    # search_class = None
    # query_interpreter_class = None
    # state_class = None
    # draft_class = None
    # result_class = None
    # action_classes = {
    #     'publish': ...
    # }


class RecordService:
    """Record Service interface."""

    _config = RecordServiceConfig

    @classmethod
    def resolver(cls):
        """Factory for creating a resolver class."""
        return cls._config.resolver_cls(
            pid_type=cls._config.pid_type,
            getter=cls._config.record_cls.get_record,
        )

    @classmethod
    def minter(cls):
        """Factory for creating a minter class."""
        return current_pidstore.minters[cls._config.pid_type]

    @classmethod
    def fetcher(cls):
        """Factory for creating a fetcher class."""
        return current_pidstore.fetchers[cls._config.pid_type]

    @classmethod
    def indexer(cls):
        """Factory for creating a indexer class."""
        return cls._config.indexer_cls()

    @classmethod
    def search_engine(cls):
        """Factory for creating a search class."""
        return cls._config.search_engine_cls(cls._config.search_cls)

    @classmethod
    def permission(cls, action_name, **kwargs):
        """Factory for creating permissions from a permission policy."""
        if cls._config.permission_policy_cls:
            return cls._config.permission_policy_cls(action_name, **kwargs)
        else:
            return Permission()

    @classmethod
    def record_cls(cls):
        """Factory for creating a record class."""
        return cls._config.record_cls

    @classmethod
    def record_state(cls, **kwargs):
        """Create a new item state."""
        return cls._config.record_state_cls(**kwargs)

    #
    # Permissions checking
    #
    @classmethod
    def require_permission(cls, identity, action_name, **kwargs):
        """Require a specific permission from the permission policy."""
        if not cls.permission(action_name, **kwargs).allows(identity):
            raise PermissionDeniedError(action_name)

    #
    # Persistent identifier resolution
    #
    @classmethod
    def resolve(cls, id_):
        """Resolve a persistent identifier to a record."""
        return cls.resolver().resolve(id_)

    #
    # High-level API
    #
    @classmethod
    def get(cls, id_, identity):
        """Retrieve a record."""
        pid, record = cls.resolve(id_)
        cls.require_permission(identity, "read", record=record)
        # Todo: how do we deal with tombstone pages
        return cls.record_state(pid=pid, record=record)

    @classmethod
    def search(cls, querystring, identity, pagination=None, *args, **kwargs):
        """Search for records matching the querystring."""
        # Permissions
        cls.require_permission(identity, "search")

        # Create search engine object
        search_engine = cls.search_engine()

        # Add search arguments
        extras = {}
        if not lt_es7:
            extras["track_total_hits"] = True

        search_engine.search_arguments(pagination=pagination, extras=extras)

        # Parse query and execute search
        query = search_engine.parse_query(querystring)
        search_result = search_engine.execute_search(query)

        # Mutate search results into a list of record states
        record_list = []
        for hit in search_result["hits"]["hits"]:
            # hit is ES AttrDict
            record = es_to_record(hit.to_dict(), cls.record_cls())
            pid = cls.fetcher()(data=record, record_uuid=None)
            record_list.append(RecordState(record=record, pid=pid))

        total = (
            search_result.hits.total
            if lt_es7
            else search_result.hits.total["value"]
        )

        aggregations = search_result.aggregations.to_dict()

        return RecordSearchState(record_list, total, aggregations)

    @classmethod
    def create(cls, data, identity):
        """Create a record."""
        # TODO: Permissions
        cls.require_permission(identity, "create")

        # Data validation
        # TODO: validate data

        # Create record
        record = cls.record_cls().create(data)
        # Mint PID
        pid = cls.minter()(record_uuid=record.id, data=record)
        # Create record state
        record_state = cls.record_state(pid=pid, record=record)
        # Persist DB
        db.session.commit()
        # Index the record
        indexer = cls.indexer()
        if indexer:
            indexer.index(record)

        return record_state

    @classmethod
    def delete(cls, id_, identity):
        """Delete a record from database and search indexes."""
        # TODO: etag and versioning

        # TODO: Removed based on id both DB and ES
        pid, record = cls.resolve(id_)
        # Permissions
        cls.require_permission(identity, "delete", record=record)

        record.delete()
        # TODO: mark all PIDs as DELETED
        db.session.commit()
        indexer = cls.indexer()
        if indexer:
            indexer.delete(record)

        # TODO: Shall it return true/false? The tombstone page?

    @classmethod
    def update(cls, id_, data, identity):
        """Replace a record."""
        # TODO: etag and versioning
        pid, record = cls.resolve(id_)
        # Permissions
        cls.require_permission(identity, "update", record=record)
        # TODO: Data validation

        record.clear()
        record.update(data)
        record.commit()
        db.session.commit()

        indexer = cls.indexer()
        if indexer:
            indexer.index(record)

        return cls.record_state(pid=pid, record=record)
