# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from flask import current_app, g
from flask_resources import CollectionResource
from flask_resources.context import resource_requestctx

from ..services import RecordService
from .record_config import RecordResourceConfig


class RecordResource(CollectionResource):
    """Record resource."""

    default_config = RecordResourceConfig

    def __init__(self, service=None, *args, **kwargs):
        """Constructor."""
        # NOTE: This constructor picks up self.default_config above
        super(RecordResource, self).__init__(*args, **kwargs)
        self.service = service or RecordService()

    #
    # Primary Interface
    #
    def search(self):
        """Perform a search over the items."""
        identity = g.identity
        querystring = resource_requestctx.request_args.pop("q", "")
        pagination = resource_requestctx.request_args

        record_search = self.service.search(
            querystring=querystring,
            identity=identity,
            pagination=pagination,
        )

        return record_search, 200

    def create(self):
        """Create an item."""
        data = resource_requestctx.request_content
        identity = g.identity
        return self.service.create(data, identity), 201

    def read(self):
        """Read an item."""
        identity = g.identity
        return (
            self.service.read(
                id_=resource_requestctx.route["pid_value"], identity=identity
            ),
            200,
        )

    def update(self):
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

    def partial_update(self):
        """Patch an item."""
        # TODO
        pass

    def delete(self):
        """Delete an item."""
        identity = g.identity
        return (
            self.service.delete(
                id_=resource_requestctx.route["pid_value"], identity=identity
            ),
            204,
        )
