# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service results."""

from flask import current_app
from marshmallow_utils.links import LinksStore

from ...config import lt_es7
from ..base import ServiceItemResult, ServiceListResult


def _current_host():
    if current_app:
        return current_app.config['SERVER_HOSTNAME']
    return None


class RecordItem(ServiceItemResult):
    """Resource unit representing pid + Record data clump."""

    def __init__(self, service, identity, record, errors=None,
                 links_config=None):
        """Constructor."""
        self._errors = errors
        self._identity = identity
        self._links_config = links_config
        self._record = record
        self._service = service
        self._data = None

    @property
    def id(self):
        """Get the record id."""
        return self._record.pid.pid_value

    def __getitem__(self, key):
        """Key a key from the data."""
        return self.data[key]

    @property
    def data(self):
        """Property to get the record."""
        if self._data:
            return self._data

        links = LinksStore(host=_current_host())

        self._data = self._service.schema.dump(
            self._identity,
            self._record,
            pid=self._record.pid,
            record=self._record,
            links_store=links
        )

        if self._links_config:
            links.resolve(config=self._links_config)

        return self._data

    def to_dict(self):
        """Get a dictionary for the record."""
        res = self.data
        if self._errors:
            res['errors'] = self._errors
        return res


class RecordList(ServiceListResult):
    """Resource list representing the result of an IdentifiedRecord search."""

    def __init__(self, service, identity, search_result, links_config=None):
        """Constructor.

        :params records: iterable of records
        :params total: total number of records
        :params aggregations: dict of ES aggregations
        :params search_args: dict(page, size, to_idx, from_idx, q)
        """
        self._identity = identity
        self._links_config = links_config
        self._results = search_result
        self._service = service

    def __len__(self):
        """Return the total numer of hits."""
        return self.total

    def __iter__(self):
        """Iterator over the hits."""
        return self.hits

    @property
    def total(self):
        """Get total number of hits."""
        if lt_es7:
            return self._results.hits.total
        else:
            return self._results.hits.total["value"]

    @property
    def aggregations(self):
        """Get the search result aggregations."""
        return self._results.aggregations.to_dict()

    @property
    def hits(self):
        """Iterator over the hits."""
        for hit in self._results.hits.hits:
            # Load dump
            record = self._service.record_cls.loads(
                hit.to_dict()['_source']
            )

            # Project the record
            links = LinksStore(host=_current_host())
            projection = self._service.schema.dump(
                self._identity,
                record,
                pid=record.pid,
                record=record,
                links_store=links,
            )

            # Create the links if needed
            if self._links_config:
                links.resolve(config=self._links_config)

            yield projection

    def to_dict(self):
        """Return result as a dictionary."""
        return{
            "hits": {
                "hits": list(self.hits),
                "total": self.total
            },
            # "links": self.links,
            "aggregations": self.aggregations
        }
