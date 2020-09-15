# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from flask import abort, g
from flask_resources import CollectionResource
from flask_resources.context import resource_requestctx

from ..config import ConfigLoaderMixin
from ..services import RecordService
from .record_config import RecordResourceConfig


class RecordResource(CollectionResource, ConfigLoaderMixin):
    """Record resource."""

    default_config = RecordResourceConfig

    def __init__(self, config=None, service=None):
        """Constructor."""
        super(RecordResource, self).__init__(config=self.load_config(config))
        self.service = service or RecordService()

    def _make_item_body(self, item_result):
        """Make the body content."""
        res = {
            'links': item_result.links.resolve(
                config=self.config.links_config),
            **item_result.record,
        }
        if item_result.errors:
            res['errors'] = item_result.errors
        return res

    def _make_list_body(self, list_result):
        """Make the body content for a list item."""
        return {
            "hits": {
                "hits": [
                    self._make_item_body(record)
                    for record in list_result.records
                ],
                "total": list_result.total
            },
            "links": list_result.links,
            "aggregations": list_result.aggregations
        }

    #
    # Primary Interface
    #
    def search(self):
        """Perform a search over the items."""
        identity = g.identity
        request_args = resource_requestctx.request_args
        querystring = request_args.pop("q", "")
        sorting = {
            k: request_args.pop(k) for k in ["sort_by", "reverse"]
            if k in request_args
        }
        pagination = request_args

        # TODO: Args parsing has to allow for easily adding new parameters,
        # when someone extends the search engine.
        record_search = self.service.search(
            identity=identity,
            querystring=querystring,
            pagination=pagination,
            sorting=sorting,
        )

        return self._make_list_body(record_search), 200

    def create(self):
        """Create an item."""
        data = resource_requestctx.request_content
        item = self.service.create(g.identity, data)
        return self._make_item_body(item), 201

    def read(self):
        """Read an item."""
        item = self.service.read(
            id_=resource_requestctx.route["pid_value"],
            identity=g.identity
        )
        return self._make_item_body(item), 200

    def update(self):
        """Update an item."""
        data = resource_requestctx.request_content
        item = self.service.update(
            id_=resource_requestctx.route["pid_value"],
            data=data,
            identity=g.identity
        )
        return self._make_item_body(item), 200

    def partial_update(self):
        """Patch an item."""
        abort(405)

    def delete(self):
        """Delete an item."""
        self.service.delete(
            id_=resource_requestctx.route["pid_value"],
            identity=g.identity
        )
        return None, 204
