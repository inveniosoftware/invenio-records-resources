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

from ..base import ServiceConfig
from ..records import RecordServiceConfig
from .results import FileMetadata, FilesMetadata, InvenioFile


#
# Configurations
#
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
    # data_schema = MarshmallowDataSchema()
    resource_unit_cls = InvenioFile  # Fake for now
    permission_policy_cls = RecordPermissionPolicy
    permission_policy_cls = RecordPermissionPolicy
    resource_unit_cls = FileMetadata  # TODO: Replace with real
    resource_list_cls = FilesMetadata  # TODO: Replace with real


class RecordFileServiceConfig(FileServiceConfig, RecordServiceConfig):
    """Service configuration for records with file support."""
