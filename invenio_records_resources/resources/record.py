# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from copy import deepcopy

from flask import current_app, g
from flask_resources import CollectionResource
from flask_resources.context import resource_requestctx
from invenio_base.utils import load_or_import_from_config

from ..services import RecordService
from .record_config import RecordResourceConfig


class RecordResource(CollectionResource):
    """Record resource."""

    config_name = None  # Must be filled with str by concrete subclasses
    default_config = RecordResourceConfig

    def __init__(self, config=None, service=None):
        """Constructor."""
        config = (
            config or
            load_or_import_from_config(
                self.config_name, default=self.default_config
            )
        )
        super(RecordResource, self).__init__(config=config)
        self.service = service or RecordService()

    #
    # Primary Interface
    #
    def search(self):
        """Perform a search over the items."""
        identity = g.identity
        request_args = deepcopy(resource_requestctx.request_args)
        querystring = request_args.pop("q", "")
        sorting = {
            k: request_args.pop(k) for k in ["sort_by", "reverse"]
            if k in request_args
        }
        pagination = {
            k: request_args.pop(k)
            for k in ["page", "size", "from_idx", "to_idx"]
            if k in request_args
        }
        # Anything left over is a facet
        faceting = request_args

        record_search = self.service.search(
            identity=identity,
            querystring=querystring,
            pagination=pagination,
            sorting=sorting,
            faceting=faceting,
        )

        return record_search, 200

    def create(self):
        """Create an item."""
        data = resource_requestctx.request_content
        identity = g.identity
        return self.service.create(identity, data), 201

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
