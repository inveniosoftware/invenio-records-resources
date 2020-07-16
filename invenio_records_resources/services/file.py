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

from .service import Service, ServiceConfig


class InvenioFile:
    """Fake File resource unit."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        pass


class FileServiceConfig(ServiceConfig):
    """File Service configuration."""

    # Don't know if any of these apply to be honest...
    # record_cls = Record
    # resolver_cls = Resolver
    # resolver_obj_type = "rec"
    # pid_type = "recid"  # PID type for resolver, minter, and fetcher
    # record_state_cls = IdentifiedRecord
    # indexer_cls = RecordIndexer
    # search_cls = RecordsSearch
    # search_engine_cls = SearchEngine
    # # Q: Do we want to keep same pattern as above and just pass classes?
    # data_validator = MarshmallowDataValidator()
    resource_unit_cls = InvenioFile  # Fake for now
    permission_policy_cls = RecordPermissionPolicy


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
        return self.resource_unit()
