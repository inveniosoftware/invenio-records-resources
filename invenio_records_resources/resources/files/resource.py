# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Record File Resources."""

from flask import abort, g
from flask_resources import CollectionResource
from flask_resources.context import resource_requestctx

from ...config import ConfigLoaderMixin
from ...services import RecordFileService
from ..actions import ActionResource
from .config import FileActionResourceConfig, FileResourceConfig


class FileResource(CollectionResource, ConfigLoaderMixin):
    """File resource."""

    default_config = FileResourceConfig

    def __init__(self, config=None, service=None):
        """Constructor."""
        super(FileResource, self).__init__(config=self.load_config(config))
        self.service = service or RecordFileService()

    # ListView GET
    def search(self, *args, **kwargs):
        """List files."""
        files = self.service.list_files(
            resource_requestctx.route["pid_value"],
            g.identity,
            links_config=self.config.links_config,
        )
        return files.to_dict(), 200

    # ListView POST
    def create(self, *args, **kwargs):
        """Initialize an upload on a record."""
        data = resource_requestctx.request_content
        item = self.service.init_files(
            resource_requestctx.route["pid_value"],
            g.identity,
            data,
            links_config=self.config.links_config,
        )
        return item.to_dict(), 201

    # TODO: see if this has to be implmented upstream
    # ListView PUT
    # PUT /api/records/:id/files
    # {
    #     'default_preview': 'article.pdf',
    #     'order': ['article.pdf', 'data.zip'],
    #     'entries': {
    #          ...
    #     }
    # }
    def update_all(self, *args, **kwargs):
        """Update top-level files metadata."""
        data = resource_requestctx.request_content
        files = self.service.update_files(
            resource_requestctx.route["pid_value"],
            g.identity,
            data,
            links_config=self.config.links_config,
        )
        return files.to_dict(), 200

    # ListView DELETE
    def delete_all(self, *args, **kwargs):
        """Delete all files."""
        self.service.delete_all_files(
            resource_requestctx.route["pid_value"],
            g.identity,
            links_config=self.config.links_config,
        )

        return None, 204

    # ItemView GET
    def read(self, *args, **kwargs):
        """Read a single file."""
        item = self.service.read_file_metadata(
            resource_requestctx.route["pid_value"],
            resource_requestctx.route["key"],
            g.identity,
            links_config=self.config.links_config,
        )
        return item.to_dict(), 200

    # ItemView PUT
    def update(self, *args, **kwargs):
        """Update the metadata a single file."""
        data = resource_requestctx.request_content
        item = self.service.update_file_metadata(
            resource_requestctx.route["pid_value"],
            resource_requestctx.route["key"],
            g.identity,
            data,
            links_config=self.config.links_config,
        )
        return item.to_dict(), 200

    # ItemView DELETE
    def delete(self, *args, **kwargs):
        """Delete a file."""
        self.service.delete_file(
            resource_requestctx.route["pid_value"],
            resource_requestctx.route["key"],
            g.identity,
            links_config=self.config.links_config,
        )

        return None, 204


# ActionResource inherits ConfigLoaderMixin
class FileActionResource(ActionResource):
    """File action resource.

    NOTE: `Commit` exists as an action to avoid having to split the
    `FileResource` into Collection + Singleton to have to POST operations.
    """

    default_config = FileActionResourceConfig

    def create_commit(self, action, operation):
        """Commit a file."""
        cmd_func = self._get_cmd_func(action, operation)
        return cmd_func(
            resource_requestctx.route["pid_value"],
            resource_requestctx.route["key"],
            g.identity,
            links_config=self.config.links_config
        )

    def read_content(self, action, operation):
        """Read file content."""
        cmd_func = self._get_cmd_func(action, operation)
        item = cmd_func(
            resource_requestctx.route["pid_value"],
            resource_requestctx.route["key"],
            g.identity,
            links_config=self.config.links_config
        )
        return item.send_file()

    def update_content(self, action, operation):
        """Upload file content."""
        cmd_func = self._get_cmd_func(action, operation)
        # TODO: Parse in `resource_requestctx`
        return cmd_func(
            resource_requestctx.route["pid_value"],
            resource_requestctx.route["key"],
            g.identity,
            stream=resource_requestctx.request_content,
            links_config=self.config.links_config
        )

    def handle_action_request(self, operation):
        """Execute an action based on an operation and the resource config."""
        action = resource_requestctx.route["action"]
        resource_func = getattr(self, f'{operation}_{action}')
        if not resource_func:
            abort(404)
        return resource_func(action, operation)
