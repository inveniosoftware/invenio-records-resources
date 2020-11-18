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
from flask_resources import CollectionResource, SingletonResource
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
        files = self.service.search(
            resource_requestctx.route["pid_value"],
            g.identity,
        )
        # FIXME: should be item.to_dict() once results are implemented
        return files, 200

    # ListView POST
    def create(self, *args, **kwargs):
        """Initialize an upload on a record."""
        data = resource_requestctx.request_content
        item = self.service.init_file(
            resource_requestctx.route["pid_value"],
            g.identity,
            data,
        )
        # FIXME: should be item.to_dict() once results are implemented
        return item, 201

    # ListView DELETE
    def delete_all(self, *args, **kwargs):
        """Delete all files."""
        self.service.delete_all_files(
            resource_requestctx.route["pid_value"],
            g.identity,
        )

        return None, 204

    # ItemView GET
    def read(self, *args, **kwargs):
        """Read a single file."""
        item = self.service.read_file_metadata(
            resource_requestctx.route["pid_value"],
            resource_requestctx.route["key"],
            g.identity,
        )
        # FIXME: should be item.to_dict() once results are implemented
        return item, 200

    # ItemView PUT
    def update(self, *args, **kwargs):
        """Update the metadata a single file."""
        abort(405)

    # ItemView DELETE
    def delete(self, *args, **kwargs):
        """Delete a file."""
        self.service.delete_file(
            resource_requestctx.route["pid_value"],
            resource_requestctx.route["key"],
            g.identity,
        )

        return None, 204


# ActionResource inherits ConfigLoaderMixin
class FileActionResource(ActionResource):
    """File action resource.

    NOTE: `Commit` exists as an action to avoid having to split the
    `FileResource` into Collection + Singleton to have to POST operations.
    """

    default_config = FileActionResourceConfig
