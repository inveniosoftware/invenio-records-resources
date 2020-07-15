# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Record File Resources."""

from flask_resources import CollectionResource, SingletonResource
from flask_resources.context import resource_requestctx
from flask_resources.resources import ResourceConfig

from ..services import FileMetadataService, FileService


class FileResourceConfig(ResourceConfig):
    """Record resource config."""

    item_route = "/records/<pid_value>/files/<key>"
    list_route = "/records/<pid_value>/files"


class FileResource(CollectionResource):
    """File resource."""

    default_config = FileResourceConfig

    def __init__(self, service=None, *args, **kwargs):
        """Constructor."""
        super(FileResource, self).__init__(*args, **kwargs)
        self.service = service or FileMetadataService()

    def search(self, *args, **kwargs):
        """List items."""
        return self.service.search(), 200

    def read(self, *args, **kwargs):
        """Read an item."""
        return self.service.read(), 200


class FileActionResourceConfig(ResourceConfig):
    """Record resource config."""

    # QUESTIONs:
    # 1- Shouldn't the item_route be used for SingletonResource actually?
    #    A change in Flask-Resource would be needed.
    # 2- Should the list_route instead precede download with "actions" to be in
    #    keeping with other actions endpoints?
    list_route = "/records/<pid_value>/files/<key>/download"


class FileActionResource(SingletonResource):
    """File action resource."""

    default_config = FileActionResourceConfig

    def __init__(self, service=None, *args, **kwargs):
        """Constructor."""
        super(FileActionResource, self).__init__(*args, **kwargs)
        self.service = service or FileService()

    def read(self, *args, **kwargs):
        """Read an item."""
        return self.service.read(), 200
