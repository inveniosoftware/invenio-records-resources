# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from ..base import Service
from .config import FileMetadataServiceConfig, FileServiceConfig


class FileService(Service):
    """File Service.

    Because actual files are not Records, it makes sense for them to have their
    own service.
    """

    default_config = FileServiceConfig

    #
    # High-level API
    #
    def read(self, id_, identity):
        """Retrieve ."""
        # TODO: IMPLEMENT ME!
        return self.result_item()


class FileMetadataService(Service):
    """File Metadata Service.

    Because file metadata isn't shaped like a Record, it makes sense for them
    to have their own service.
    """

    default_config = FileMetadataServiceConfig

    #
    # High-level API
    #
    def read(self, id_, identity):
        """Retrieve ."""
        # TODO: IMPLEMENT ME!
        return self.result_item()

    def search(self, querystring, identity, pagination=None, *args, **kwargs):
        """Search for records matching the querystring."""
        # TODO: IMPLEMENT ME!
        return self.result_list()
