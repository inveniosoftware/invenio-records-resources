# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Resources module to create REST APIs."""

from flask_resources import CollectionResource
from flask_resources.context import resource_requestctx
from flask_resources.loaders import RequestLoader
from flask_resources.parsers import search_request_parser
from flask_resources.resources import ResourceConfig
from invenio_records_agent import RecordManager

from ..responses import RecordResponse
from ..schemas import RecordSchemaJSONV1
from ..serializers import RecordJSONSerializer


class RecordResourceConfig(ResourceConfig):
    """Record resource config."""

    item_route = "/records_v2/<pid_value>"
    list_route = "/records_v2"
    response_handlers = {
        "application/json": RecordResponse(
            RecordJSONSerializer(schema=RecordSchemaJSONV1)
        )
    }


class RecordResource(CollectionResource):
    """Record resource."""

    def __init__(
        self,
        config=RecordResourceConfig(),
        manager_cls=RecordManager,
        *args,
        **kwargs
    ):
        """Constructor."""
        super(RecordResource, self).__init__(config=config, *args, **kwargs)
        self.manager_cls = manager_cls

    #
    # Primary Interface
    #
    def search(self, *args, **kwargs):
        """Perform a search over the items."""
        # TODO fix identity extraction
        identity = None
        record_list, total, aggregations = self.manager_cls.search(
            querystring=resource_requestctx.request_args.get("q", ""),
            identity=identity,
            pagination=resource_requestctx.request_args.get(
                "pagination", None
            ),
        )

        return record_list, 200

    def create(self, *args, **kwargs):
        """Create an item."""
        data = resource_requestctx.request_content
        # TODO fix identity extraction
        identity = None
        return self.manager_cls.create(data, identity), 200

    def read(self, *args, **kwargs):
        """Read an item."""
        identity = None
        return (
            self.manager_cls.get(
                id_=resource_requestctx.route["pid_value"], identity=identity
            ),
            200,
        )

    def update(self, *args, **kwargs):
        """Update an item."""
        # TODO
        pass

    def partial_update(self, *args, **kwargs):
        """Patch an item."""
        # TODO
        pass

    def delete(self, *args, **kwargs):
        """Delete an item."""
        # TODO
        pass
