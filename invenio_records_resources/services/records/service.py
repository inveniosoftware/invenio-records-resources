# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2020 European Union.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from flask import current_app
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_permissions.api import permission_filter
from invenio_search import current_search_client
from invenio_search.engine import dsl
from kombu import Queue
from werkzeug.local import LocalProxy

from invenio_records_resources.services.errors import PermissionDeniedError

from ..base import LinksTemplate, Service
from ..errors import RevisionIdMismatchError
from ..uow import RecordCommitOp, RecordDeleteOp, unit_of_work
from .schema import ServiceSchemaWrapper


class RecordIndexerMixin:
    """Mixin class to define record indexer.

    Can be mixed in RecordService classes with the corresponding
    configuration attributes.
    """

    @property
    def indexer(self):
        """Factory for creating an indexer instance."""
        return self.config.indexer_cls(
            # the routing key is mandatory in the indexer constructor since
            # it is afterwards passed explicitly to the created consumers
            # and producers. this means that it is not strictly necessary to
            # pass it to the queue constructor. however, it is passed for
            # consistency (in case the queue is used by itself) and to help
            # entity declaration on publish.
            queue=LocalProxy(
                lambda: Queue(
                    self.config.indexer_queue_name,
                    exchange=current_app.config["INDEXER_MQ_EXCHANGE"],
                    routing_key=self.config.indexer_queue_name,
                )
            ),
            routing_key=self.config.indexer_queue_name,
            record_cls=self.config.record_cls,
            record_to_index=self.record_to_index,
            record_dumper=self.config.index_dumper,
        )

    def record_to_index(self, record):
        """Function used to map a record to an index."""
        return record.index._name


class RecordService(Service, RecordIndexerMixin):
    """Record Service."""

    #
    # Low-level API
    #

    @property
    def schema(self):
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    @property
    def components(self):
        """Return initialized service components."""
        return (c(self) for c in self.config.components)

    @property
    def record_cls(self):
        """Factory for creating a record class."""
        return self.config.record_cls

    @property
    def links_item_tpl(self):
        """Item links template."""
        return LinksTemplate(
            self.config.links_item,
        )

    @property
    def expandable_fields(self):
        """Get expandable fields.

        Override this method when needed.
        """
        return []

    def check_revision_id(self, record, expected_revision_id):
        """Validate the given revision_id with current record's one.

        :param record: The record object.
        :param int expected_revision_id: Expected revision id to be found in
            record.
        :raises services.errors.RevisionIdMismatchError: If the
            condition is not met.
        """
        if (
            expected_revision_id is not None
            and record.revision_id != expected_revision_id
        ):
            raise RevisionIdMismatchError(record.revision_id, expected_revision_id)

    def create_search(
        self,
        identity,
        record_cls,
        search_opts,
        permission_action="read",
        preference=None,
        extra_filter=None,
        versioning=True,
    ):
        """Instantiate a search class."""
        if permission_action:
            permission = self.permission_policy(
                action_name=permission_action, identity=identity
            )
        else:
            permission = None

        default_filter = permission_filter(permission)
        if extra_filter is not None:
            default_filter = default_filter & extra_filter

        search = search_opts.search_cls(
            using=current_search_client,
            default_filter=default_filter,
            index=record_cls.index.search_alias,
        )

        search = (
            search
            # Avoid query bounce problem
            .with_preference_param(preference)
        )

        if versioning:
            search = (
                search
                # Add document version to search response
                .params(version=True)
            )

        # Extras
        extras = {}
        extras["track_total_hits"] = True
        search = search.extra(**extras)

        return search

    def search_request(
        self,
        identity,
        params,
        record_cls,
        search_opts,
        preference=None,
        extra_filter=None,
        permission_action="read",
        versioning=True,
    ):
        """Factory for creating a Search DSL instance."""
        search = self.create_search(
            identity,
            record_cls,
            search_opts,
            permission_action=permission_action,
            preference=preference,
            extra_filter=extra_filter,
            versioning=versioning,
        )

        # Run search args evaluator
        for interpreter_cls in search_opts.params_interpreters_cls:
            search = interpreter_cls(search_opts).apply(identity, search, params)

        return search

    def _search(
        self,
        action,
        identity,
        params,
        search_preference,
        record_cls=None,
        search_opts=None,
        extra_filter=None,
        permission_action="read",
        versioning=True,
        **kwargs,
    ):
        """Create the search engine DSL."""
        # Merge params
        # NOTE: We allow using both the params variable, as well as kwargs. The
        # params is used by the resource, and kwargs is used to have an easier
        # programatic interface .search(idty, q='...') instead of
        # .search(idty, params={'q': '...'}).
        params.update(kwargs)

        # Create an search engine DSL
        search = self.search_request(
            identity,
            params,
            record_cls or self.record_cls,
            search_opts or self.config.search,
            preference=search_preference,
            extra_filter=extra_filter,
            permission_action=permission_action,
            versioning=versioning,
        )

        # Run components
        for component in self.components:
            if hasattr(component, action):
                search = getattr(component, action)(identity, search, params)
        return search

    #
    # High-level API
    #
    def search(
        self, identity, params=None, search_preference=None, expand=False, **kwargs
    ):
        """Search for records matching the querystring."""
        self.require_permission(identity, "search")

        # Prepare and execute the search
        params = params or {}
        search = self._search("search", identity, params, search_preference, **kwargs)
        search_result = search.execute()

        return self.result_list(
            self,
            identity,
            search_result,
            params,
            links_tpl=LinksTemplate(self.config.links_search, context={"args": params}),
            links_item_tpl=self.links_item_tpl,
            expandable_fields=self.expandable_fields,
            expand=expand,
        )

    def scan(self, identity, params=None, search_preference=None, **kwargs):
        """Scan for records matching the querystring."""
        self.require_permission(identity, "search")

        # Prepare and execute the search as scan()
        params = params or {}
        search_result = self._search(
            "scan", identity, params, search_preference, **kwargs
        ).scan()

        return self.result_list(
            self,
            identity,
            search_result,
            params,
            links_tpl=None,
            links_item_tpl=self.links_item_tpl,
        )

    def reindex(
        self, identity, params=None, search_preference=None, search_query=None, **kwargs
    ):
        """Reindex records matching the query parameters."""
        self.require_permission(identity, "search")

        # prepare and update query
        params = params or {}
        params.update(kwargs)

        # create a search engine DSL, we do not want components to run
        search = self.search_request(
            identity,
            params,
            self.record_cls,
            self.config.search,
            preference=search_preference,
        ).source(
            False
        )  # get only the uuid of the records

        if search_query:  # incompatible with params={"q":...}
            search = search.query(search_query)

        search_result = search.scan()
        iterable_ids = (res.meta.id for res in search_result)

        self.indexer.bulk_index(iterable_ids)
        return True

    @unit_of_work()
    def create(self, identity, data, uow=None, expand=False):
        """Create a record.

        :param identity: Identity of user creating the record.
        :param data: Input data according to the data schema.
        """
        return self._create(self.record_cls, identity, data, uow=uow, expand=expand)

    @unit_of_work()
    def _create(
        self, record_cls, identity, data, raise_errors=True, uow=None, expand=False
    ):
        """Create a record.

        :param identity: Identity of user creating the record.
        :param dict data: Input data according to the data schema.
        :param bool raise_errors: raise schema ValidationError or not.
        """
        self.require_permission(identity, "create")

        # Validate data and create record with pid
        data, errors = self.schema.load(
            data,
            context={"identity": identity},
            raise_errors=raise_errors  # if False, flow is continued with data
            # only containing valid data, but errors
            # are reported (as warnings)
        )

        # It's the components who saves the actual data in the record.
        record = record_cls.create({})

        # Run components
        self.run_components(
            "create",
            identity,
            data=data,
            record=record,
            errors=errors,
            uow=uow,
        )

        # Persist record (DB and index)
        uow.register(RecordCommitOp(record, self.indexer))

        return self.result_item(
            self,
            identity,
            record,
            links_tpl=self.links_item_tpl,
            errors=errors,
            expandable_fields=self.expandable_fields,
            expand=expand,
        )

    def read(self, identity, id_, expand=False):
        """Retrieve a record."""
        # Resolve and require permission
        record = self.record_cls.pid.resolve(id_)
        self.require_permission(identity, "read", record=record)

        # Run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, record=record)

        return self.result_item(
            self,
            identity,
            record,
            links_tpl=self.links_item_tpl,
            expandable_fields=self.expandable_fields,
            expand=expand,
        )

    def exists(self, identity, id_):
        """Check if the record exists and user has permission."""
        try:
            record = self.record_cls.pid.resolve(id_)
            self.require_permission(identity, "read", record=record)
            return True
        except (PIDDoesNotExistError, PermissionDeniedError):
            return False

    def _read_many(
        self,
        identity,
        search_query,
        fields=None,
        max_records=150,
        record_cls=None,
        search_opts=None,
        extra_filter=None,
        preference=None,
        **kwargs,
    ):
        """Search for records matching the ids."""
        # We use create_search() to avoid the overhead of aggregations etc
        # being added to the query with using search_request().
        search = self.create_search(
            identity=identity,
            record_cls=record_cls or self.record_cls,
            search_opts=search_opts or self.config.search,
            permission_action="search",
            preference=preference,
            extra_filter=extra_filter,
            versioning=True,
        )

        # Fetch only certain fields - explicitly add internal system fields
        # required to use the result list to dump the output.
        if fields:
            dumper_fields = ["uuid", "version_id", "created", "updated", "expires_at"]
            fields = fields + dumper_fields
            # ES 7.11+ supports a more efficient way of fetching only certain
            # fields using the "fields"-option to a query. However, ES 7 and
            # OS 1 versions does not support it, so we use the source filtering
            # method instead for now.
            search = search.source(fields)

        search = search[0:max_records]
        search_result = search.query(search_query).execute()

        return search_result

    def read_many(self, identity, ids, fields=None, **kwargs):
        """Search for records matching the ids."""
        clauses = []
        for id_ in ids:
            clauses.append(dsl.Q("term", **{"id": id_}))
        query = dsl.Q("bool", minimum_should_match=1, should=clauses)

        results = self._read_many(identity, query, fields, len(ids), **kwargs)

        return self.result_list(self, identity, results)

    def read_all(self, identity, fields, max_records=150, **kwargs):
        """Search for records matching the querystring."""
        search_query = dsl.Q("match_all")
        results = self._read_many(identity, search_query, fields, max_records, **kwargs)

        return self.result_list(self, identity, results)

    @unit_of_work()
    def update(self, identity, id_, data, revision_id=None, uow=None, expand=False):
        """Replace a record."""
        record = self.record_cls.pid.resolve(id_)

        self.check_revision_id(record, revision_id)

        # Permissions
        self.require_permission(identity, "update", record=record)

        data, _ = self.schema.load(
            data, context=dict(identity=identity, pid=record.pid, record=record)
        )

        # Run components
        self.run_components("update", identity, data=data, record=record, uow=uow)

        uow.register(RecordCommitOp(record, self.indexer))

        return self.result_item(
            self,
            identity,
            record,
            links_tpl=self.links_item_tpl,
            expandable_fields=self.expandable_fields,
            expand=expand,
        )

    @unit_of_work()
    def delete(self, identity, id_, revision_id=None, uow=None):
        """Delete a record from database and search indexes."""
        record = self.record_cls.pid.resolve(id_)

        self.check_revision_id(record, revision_id)

        # Permissions
        self.require_permission(identity, "delete", record=record)

        # Run components
        self.run_components("delete", identity, record=record, uow=uow)

        uow.register(RecordDeleteOp(record, self.indexer, index_refresh=True))

        return True

    def rebuild_index(self, identity, uow=None):
        """Reindex all records managed by this service.

        Note: Skips (soft) deleted records.
        """
        model_cls = self.record_cls.model_cls
        records = (
            db.session.query(model_cls.id)
            .filter(model_cls.is_deleted == False)
            .yield_per(1000)
        )

        self.indexer.bulk_index((rec.id for rec in records))

        return True

    #
    # notification handlers
    #
    def on_relation_update(self, identity, record_type, records_info, notif_time):
        """Handles the update of a related field record."""
        fieldpaths = self.config.relations.get(record_type, [])
        clauses = []
        for field in fieldpaths:
            for record in records_info:
                recid, uuid, revision_id = record
                clauses.append(
                    dsl.Q(
                        "bool",
                        must=[dsl.Q("term", **{f"{field}.id": recid})],
                        must_not=[
                            dsl.Q("term", **{f"{field}.@v": f"{uuid}::{revision_id}"})
                        ],
                    )
                )

        filter = [dsl.Q("range", indexed_at={"lte": notif_time})]
        search_query = dsl.Q(
            "bool", minimum_should_match=1, should=clauses, filter=filter
        )

        self.reindex(identity, search_query=search_query)
        return True
