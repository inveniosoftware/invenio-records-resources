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
from marshmallow_utils.links import LinksFactory

from ...config import lt_es7
from ...pagination import Pagination
from ..base import ServiceItemResult, ServiceListResult


def _current_host():
    """Function used to provide the current hostname to the link store."""
    if current_app:
        return current_app.config['SITE_HOSTNAME']
    return None


class RecordItem(ServiceItemResult):
    """Single record result."""

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

        links = LinksFactory(host=_current_host, config=self._links_config)

        self._data = self._service.schema.dump(
            self._identity,
            self._record,
            links_namespace="record",
            links_factory=links,
        )

        return self._data

    def to_dict(self):
        """Get a dictionary for the record."""
        res = self.data
        if self._errors:
            res['errors'] = self._errors
        return res


class RecordList(ServiceListResult):
    """List of records result."""

    def __init__(self, service, identity, results, params,
                 links_config=None):
        """Constructor.

        :params service: a service instance
        :params identity: an identity that performed the service request
        :params results: the search results
        :params params: dictionary of the query parameters
        :params links_config: a links store config
        """
        self._identity = identity
        self._links_config = links_config
        self._results = results
        self._service = service
        self._params = params

    def __len__(self):
        """Return the total numer of hits."""
        return self.total

    def __iter__(self):
        """Iterator over the hits."""
        return self.hits

    @property
    def total(self):
        """Get total number of hits."""
        if hasattr(self._results, 'hits'):
            if lt_es7:
                return self._results.hits.total
            else:
                return self._results.hits.total["value"]
        else:
            # handle scan(): returns a generator
            return None

    @property
    def aggregations(self):
        """Get the search result aggregations."""
        return self._results.aggregations.to_dict()

    @property
    def hits(self):
        """Iterator over the hits."""
        links = LinksFactory(host=_current_host, config=self._links_config)

        for hit in self._results:
            # Load dump
            record = self._service.record_cls.loads(hit.to_dict())

            # Project the record
            projection = self._service.schema.dump(
                self._identity,
                record,
                pid=record.pid,
                record=record,
                links_namespace="record",
                links_factory=links
            )

            yield projection

    @property
    def pagination(self):
        """Create a pagination object."""
        return Pagination(
            self._params['size'],
            self._params['page'],
            self.total,
        )

    @property
    def links(self):
        """Get the search result links.

        TODO: Would be nicer if this were a parallel of data above.
        """
        links = LinksFactory(host=_current_host, config=self._links_config)
        schema = self._service.schema_search_links

        data = schema.dump(
            self._identity,
            # It ain't pretty but it will do
            {**self._params, "_pagination": self.pagination},
            links_factory=links,
            links_namespace="search",
        )

        return data.get("links")

    def to_dict(self):
        """Return result as a dictionary."""
        res = {
            "hits": {
                "hits": list(self.hits),
                "total": self.total,
            },
            "links": self.links,
            "sortBy": self._params["sort"],
            "aggregations": self.aggregations,
        }
        if res['links'] is None:
            del res['links']
        return res
