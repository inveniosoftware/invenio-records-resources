# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from invenio_records_permissions.policies.records import RecordPermissionPolicy

from ..resource_units import IdentifiedRecord, IdentifiedRecords
from .service import Service, ServiceConfig


class FileMetadata:
    """TODO: Replace this fake File metadata resource unit."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        pass


class FilesMetadata:
    """TODO: Replace this fake File metadata resource list."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        pass


class FileMetadataServiceConfig(ServiceConfig):
    """File Metadata Service configuration."""

    # Configurations that are in common
    permission_policy_cls = RecordPermissionPolicy
    resource_unit_cls = FileMetadata  # TODO: Replace with real
    resource_list_cls = FilesMetadata  # TODO: Replace with real


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
        return self.resource_unit_cls()

    def search(self, querystring, identity, pagination=None, *args, **kwargs):
        """Search for records matching the querystring."""
        # TODO: IMPLEMENT ME!
        return self.resource_list_cls()
