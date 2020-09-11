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

from ..services import FileMetadataService, FileService
from .file_config import FileActionResourceConfig, FileResourceConfig


class FileResource(CollectionResource):
    """File resource."""

    default_config = FileResourceConfig

    def __init__(self, config=None, service=None):
        """Constructor."""
        super().__init__(config=self.load_config(config))
        self.service = service or FileMetadataService()

    def search(self, *args, **kwargs):
        """List items."""
        return self.service.search(), 200

    def read(self, *args, **kwargs):
        """Read an item."""
        return self.service.read(), 200


class FileActionResource(SingletonResource):
    """File action resource."""

    default_config = FileActionResourceConfig

    def __init__(self, config=None, service=None):
        """Constructor."""
        super().__init__(config=self.load_config(config))
        self.service = service or FileService()

    def read(self, *args, **kwargs):
        """Read an item."""
        return self.service.read(), 200
