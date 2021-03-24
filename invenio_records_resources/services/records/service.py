# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2020 European Union.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from invenio_db import db
from invenio_records_permissions.api import permission_filter
from invenio_search import current_search_client

from ...config import lt_es7
from ..base import LinksTemplate, Service
from ..errors import RevisionIdMismatchError
from .schema import ServiceSchemaWrapper


class RecordService(Service):
    """Record Service."""

    #
    # Low-level API
    #
    @property
    def indexer(self):
        """Factory for creating an indexer instance."""
        return self.config.indexer_cls(
            record_cls=self.config.record_cls,
            record_to_index=self.record_to_index,
            record_dumper=self.config.index_dumper,
        )

    def record_to_index(self, record):
        """Function used to map a record to an index."""
        # We are returning "_doc" as document type as recommended by
        # Elasticsearch documentation to have v6.x and v7.x equivalent. In v8
        # document types will have been completely removed.
        return record.index._name, '_doc'

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

    def check_revision_id(self, record, expected_revision_id):
        """Validate the given revision_id with current record's one.

        :param record: The record object.
        :param int expected_revision_id: Expected revision id to be found in
            record.
        :raises services.errors.RevisionIdMismatchError: If the
            condition is not met.
        """
        if expected_revision_id is not None \
           and record.revision_id != expected_revision_id:
            raise RevisionIdMismatchError(
                record.revision_id, expected_revision_id
            )

    def create_search(self, identity, record_cls, search_opts,
                      permission_action='read', preference=None,
                      extra_filter=None):
        """Instantiate a search class."""
        permission = self.permission_policy(
            action_name=permission_action, identity=identity)

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
            # Add document version to ES response
            .params(version=True)
        )

        # Extras
        extras = {}
        if not lt_es7:
            extras["track_total_hits"] = True
        search = search.extra(**extras)

        return search

    def search_request(self, identity, params, record_cls, search_opts,
                       preference=None, extra_filter=None,
                       permission_action='read'):
        """Factory for creating a Search DSL instance."""
        search = self.create_search(
            identity,
            record_cls,
            search_opts,
            permission_action=permission_action,
            preference=preference,
            extra_filter=extra_filter,
        )

        # Run search args evaluator
        for interpreter_cls in search_opts.params_interpreters_cls:
            search = interpreter_cls(search_opts).apply(
                identity, search, params
            )

        return search

    def _search(self, action, identity, params, es_preference, record_cls=None,
                search_opts=None, extra_filter=None, permission_action='read',
                **kwargs):
        """Create the Elasticsearch DSL."""
        # Merge params
        # NOTE: We allow using both the params variable, as well as kwargs. The
        # params is used by the resource, and kwargs is used to have an easier
        # programatic interface .search(idty, q='...') instead of
        # .search(idty, params={'q': '...'}).
        params.update(kwargs)

        # Create an Elasticsearch DSL
        search = self.search_request(
            identity,
            params,
            record_cls or self.record_cls,
            search_opts or self.config.search,
            preference=es_preference,
            extra_filter=extra_filter,
            permission_action=permission_action,
        )

        # Run components
        for component in self.components:
            if hasattr(component, action):
                search = getattr(component, action)(identity, search, params)
        return search

    #
    # High-level API
    #
    def search(self, identity, params=None, es_preference=None, **kwargs):
        """Search for records matching the querystring."""
        self.require_permission(identity, 'search')

        # Prepare and execute the search
        params = params or {}
        search_result = self._search(
            'search', identity, params, es_preference, **kwargs).execute()

        return self.result_list(
            self,
            identity,
            search_result,
            params,
            links_tpl=LinksTemplate(self.config.links_search, context={
                "args": params
            }),
            links_item_tpl=self.links_item_tpl,
        )

    def scan(self, identity, params=None, es_preference=None, **kwargs):
        """Scan for records matching the querystring."""
        self.require_permission(identity, 'search')

        # Prepare and execute the search as scan()
        params = params or {}
        search_result = self._search(
            'scan', identity, params, es_preference, **kwargs).scan()

        return self.result_list(
            self,
            identity,
            search_result,
            params,
            links_tpl=None,
            links_item_tpl=self.links_item_tpl,
        )

    def reindex(self, identity, params=None, es_preference=None, **kwargs):
        """Reindex records matching the query parameters."""
        self.require_permission(identity, 'search')

        # Prepare and execute the search as scan()
        params = params or {}
        search_result = self._search(
            'reindex', identity, params, es_preference, **kwargs).scan()

        iterable_ids = (res.id for res in search_result)

        self.indexer.bulk_index(iterable_ids)
        return True

    def create(self, identity, data):
        """Create a record.

        :param identity: Identity of user creating the record.
        :param data: Input data according to the data schema.
        """
        return self._create(self.record_cls, identity, data)

    def _create(self, record_cls, identity, data, raise_errors=True):
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
            links_tpl=self.links_item_tpl,
            errors=errors
        )

    def read(self, id_, identity):
        """Retrieve a record."""
        # Resolve and require permission
        record = self.record_cls.pid.resolve(id_)
        self.require_permission(identity, "read", record=record)

        # Run components
        for component in self.components:
            if hasattr(component, 'read'):
                component.read(identity, record=record)

        return self.result_item(
            self,
            identity,
            record,
            links_tpl=self.links_item_tpl,
        )

    def update(self, id_, identity, data, revision_id=None):
        """Replace a record."""
        record = self.record_cls.pid.resolve(id_)

        self.check_revision_id(record, revision_id)

        # Permissions
        self.require_permission(identity, "update", record=record)

        data, _ = self.schema.load(
            data,
            context=dict(
                identity=identity,
                pid=record.pid,
                record=record
            )
        )

        # Run components
        for component in self.components:
            if hasattr(component, 'update'):
                component.update(identity, data=data, record=record)

        record.commit()
        db.session.commit()

        if self.indexer:
            self.indexer.index(record)

        return self.result_item(
            self,
            identity,
            record,
            links_tpl=self.links_item_tpl,
        )

    def delete(self, id_, identity, revision_id=None):
        """Delete a record from database and search indexes."""
        record = self.record_cls.pid.resolve(id_)

        self.check_revision_id(record, revision_id)

        # Permissions
        self.require_permission(identity, "delete", record=record)

        # Run components
        for component in self.components:
            if hasattr(component, 'delete'):
                component.delete(identity, record=record)

        record.delete()
        db.session.commit()

        if self.indexer:
            self.indexer.delete(record, refresh=True)

        return True

    def rebuild_index(self, identity):
        """Reindex all records managed by this service.

        Note: Skips (soft) deleted records.
        """
        for rec_meta in self.record_cls.model_cls.query.all():
            rec = self.record_cls(rec_meta.data, model=rec_meta)

            if not rec.is_deleted:
                self.indexer.index(rec)

        return True
