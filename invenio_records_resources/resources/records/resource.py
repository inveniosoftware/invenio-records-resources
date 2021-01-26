# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

import hashlib

from flask import abort, g, request
from flask_resources import CollectionResource
from flask_resources.context import resource_requestctx

from ...config import ConfigLoaderMixin
from ...services import RecordService
from .config import RecordResourceConfig


class RecordResource(CollectionResource, ConfigLoaderMixin):
    """Record resource."""

    default_config = RecordResourceConfig

    def __init__(self, config=None, service=None):
        """Constructor."""
        super(RecordResource, self).__init__(config=self.load_config(config))
        self.service = service or RecordService()

    def _get_es_preference(self):
        user_agent = request.headers.get('User-Agent', '')
        ip = request.remote_addr
        user_hash = f"{ip}-{user_agent}".encode('utf8')
        alg = hashlib.md5()
        alg.update(user_hash)
        return alg.hexdigest()

    #
    # Primary Interface
    #
    def search(self):
        """Perform a search over the items."""
        identity = g.identity
        hits = self.service.search(
            identity=identity,
            params=resource_requestctx.url_args,
            links_config=self.config.links_config,
            es_preference=self._get_es_preference()
        )
        return hits.to_dict(), 200

    def create(self):
        """Create an item."""
        data = resource_requestctx.request_content
        item = self.service.create(
            g.identity, data, links_config=self.config.links_config)
        return item.to_dict(), 201

    def read(self):
        """Read an item."""
        item = self.service.read(
            resource_requestctx.route["pid_value"],
            g.identity,
            links_config=self.config.links_config,
        )
        return item.to_dict(), 200

    def update(self):
        """Update an item."""
        data = resource_requestctx.request_content
        item = self.service.update(
            resource_requestctx.route["pid_value"],
            g.identity,
            data,
            links_config=self.config.links_config,
            revision_id=resource_requestctx.headers.get("if_match"),
        )
        return item.to_dict(), 200

    def partial_update(self):
        """Patch an item."""
        abort(405)

    def delete(self):
        """Delete an item."""
        self.service.delete(
            resource_requestctx.route["pid_value"],
            g.identity,
            revision_id=resource_requestctx.headers.get("if_match"),
        )
        return None, 204
