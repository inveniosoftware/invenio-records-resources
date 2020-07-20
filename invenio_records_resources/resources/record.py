# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from flask import g
from flask_resources import CollectionResource
from flask_resources.context import resource_requestctx
from flask_resources.loaders import RequestLoader
from flask_resources.resources import ResourceConfig

from ..responses import RecordResponse
from ..schemas import RecordSchemaJSONV1
from ..serializers import RecordJSONSerializer
from ..services import RecordService


class RecordResourceConfig(ResourceConfig):
    """Record resource config."""

    item_route = "/records/<pid_value>"
    list_route = "/records"
    response_handlers = {
        "application/json": RecordResponse(
            RecordJSONSerializer(schema=RecordSchemaJSONV1)
        )
    }


class RecordResource(CollectionResource):
    """Record resource."""

    default_config = RecordResourceConfig

    def __init__(self, service=None, *args, **kwargs):
        """Constructor."""
        super(RecordResource, self).__init__(*args, **kwargs)
        self.service = service or RecordService()

    #
    # Primary Interface
    #
    def search(self, *args, **kwargs):
        """Perform a search over the items."""
        identity = g.identity
        record_search = self.service.search(
            querystring=resource_requestctx.request_args.get("q", ""),
            identity=identity,
            pagination=resource_requestctx.request_args.get("pagination"),
        )

        return record_search, 200

    def create(self, *args, **kwargs):
        """Create an item."""
        data = resource_requestctx.request_content
        identity = g.identity
        return self.service.create(data, identity), 201

    def read(self, *args, **kwargs):
        """Read an item."""
        identity = g.identity
        return (
            self.service.read(
                id_=resource_requestctx.route["pid_value"], identity=identity
            ),
            200,
        )

    def update(self, *args, **kwargs):
        """Update an item."""
        data = resource_requestctx.request_content
        identity = g.identity
        return (
            self.service.update(
                id_=resource_requestctx.route["pid_value"],
                data=data,
                identity=identity
            ),
            200,
        )

    def partial_update(self, *args, **kwargs):
        """Patch an item."""
        # TODO
        pass

    def delete(self, *args, **kwargs):
        """Delete an item."""
        identity = g.identity
        return (
            self.service.delete(
                id_=resource_requestctx.route["pid_value"], identity=identity
            ),
            204,
        )
