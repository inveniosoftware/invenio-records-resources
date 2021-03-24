# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

import marshmallow as ma
from flask import g
from flask_resources import Resource, from_conf, request_body_parser, \
    request_parser, resource_requestctx, response_handler, route

from ..errors import ErrorHandlersMixin
from .utils import es_preference

#
# Decorators
#
request_data = request_body_parser(
    parsers=from_conf('request_body_parsers'),
    default_content_type=from_conf('default_content_type')
)

request_view_args = request_parser(
    from_conf('request_view_args'), location='view_args'
)

request_headers = request_parser(
    {"if_match": ma.fields.Int()}, location='headers'
)

request_search_args = request_parser(
    from_conf('request_args'), location='args'
)


#
# Resource
#
class RecordResource(ErrorHandlersMixin, Resource):
    """Record resource."""

    def __init__(self, config, service):
        """Constructor."""
        super(RecordResource, self).__init__(config)
        self.service = service

    def create_url_rules(self):
        """Create the URL rules for the record resource."""
        routes = self.config.routes
        return [
            route("GET", routes["list"], self.search),
            route("POST", routes["list"], self.create),
            route("GET", routes["item"], self.read),
            route("PUT", routes["item"], self.update),
            route("DELETE", routes["item"], self.delete),
        ]

    #
    # Primary Interface
    #
    @request_search_args
    @response_handler(many=True)
    def search(self):
        """Perform a search over the items."""
        identity = g.identity
        hits = self.service.search(
            identity=identity,
            params=resource_requestctx.args,
            es_preference=es_preference()
        )
        return hits.to_dict(), 200

    @request_data
    @response_handler()
    def create(self):
        """Create an item."""
        item = self.service.create(
            g.identity,
            resource_requestctx.data or {},
        )
        return item.to_dict(), 201

    @request_view_args
    @response_handler()
    def read(self):
        """Read an item."""
        item = self.service.read(
            resource_requestctx.view_args["pid_value"],
            g.identity,
        )
        return item.to_dict(), 200

    @request_headers
    @request_view_args
    @request_data
    @response_handler()
    def update(self):
        """Update an item."""
        item = self.service.update(
            resource_requestctx.view_args["pid_value"],
            g.identity,
            resource_requestctx.data,
            revision_id=resource_requestctx.headers.get("if_match"),
        )
        return item.to_dict(), 200

    @request_headers
    @request_view_args
    def delete(self):
        """Delete an item."""
        self.service.delete(
            resource_requestctx.view_args["pid_value"],
            g.identity,
            revision_id=resource_requestctx.headers.get("if_match"),
        )
        return "", 204
