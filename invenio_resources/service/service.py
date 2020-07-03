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
from .state import RecordState


class RecordServiceConfig:
    """Service configuration."""

    record_cls = Record
    resolver_cls = Resolver
    resolver_obj_type = "rec"
    pid_type = "recid"  # PID type for resolver and minter
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


class RecordServiceFactory:
    """Factory for creating object instances and classes."""

    def __init__(self, config):
        """Constructor."""
        self._config = config

    def resolver(self):
        """Factory for creating a resolver class."""
        return self._config.resolver_cls(
            pid_type=self._config.pid_type,
            getter=self._config.record_cls.get_record,
        )

    def minter(self):
        """Factory for creating a minter class."""
        return current_pidstore.minters[self._config.pid_type]

    def fetcher(self):
        """Factory for creating a fetcher class."""
        return current_pidstore.fetchers[self._config.pid_type]

    def indexer(self):
        """Factory for creating a indexer class."""
        return self._config.indexer_cls()

    def search(self):
        """Factory for creating a search class."""
        return self._config.search_engine_cls(self._config.search_cls)

    def permission(self, action_name, **kwargs):
        """Factory for creating permissions from a permission policy."""
        if self._config.permission_policy_cls:
            return self._config.permission_policy_cls(action_name, **kwargs)
        else:
            return Permission()

    def record(self):
        """Factory for creating a record class."""
        return self._config.record_cls

    def record_state(self, **kwargs):
        """Create a new item state."""
        return self._config.record_state_cls(**kwargs)


class RecordService:
    """Record Service interface."""

    factory = RecordServiceFactory(RecordServiceConfig)

    #
    # Permissions checking
    #
    @classmethod
    def require_permission(cls, identity, action_name, **kwargs):
        """Require a specific permission from the permission policy."""
        if not cls.factory.permission(action_name, **kwargs).allows(identity):
            raise PermissionDeniedError(action_name)

    #
    # Persistent identifier resolution
    #
    @classmethod
    def resolve(cls, id_):
        """Resolve a persistent identifier to a record."""
        return cls.factory.resolver().resolve(id_)

    #
    # High-level API
    #
    @classmethod
    def get(cls, id_, identity):
        """Retrieve a record."""
        pid, record = cls.resolve(id_)
        cls.require_permission(identity, "read", record=record)
        # Todo: how do we deal with tombstone pages
        return cls.factory.record_state(pid=pid, record=record)

    @classmethod
    def search(cls, querystring, identity, pagination=None, *args, **kwargs):
        """Search for records matching the querystring."""
        # Create search object
        search_engine = cls.factory.search()

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
            record = es_to_record(hit.to_dict(), cls.factory.record())
            pid = cls.factory.fetcher()(data=record, record_uuid=None)
            record_list.append(RecordState(record=record, pid=pid))

        total = (
            search_result.hits.total
            if lt_es7
            else search_result.hits.total["value"]
        )

        aggregations = search_result.aggregations.to_dict()

        return record_list, total, aggregations

    @classmethod
    def create(cls, data, identity):
        """Create a record."""
        # Permissions
        # cls.require_permission(identity, "create")
        # Data validation
        # TODO: validate data

        # Create record
        record = cls.factory.record().create(data)
        # Mint PID
        pid = cls.factory.minter()(record_uuid=record.id, data=record)
        # Create record state
        record_state = cls.factory.record_state(pid=pid, record=record)
        # Persist DB
        db.session.commit()
        # Index the record
        indexer = cls.factory.indexer()
        if indexer:
            indexer.index(record)

        return record_state
