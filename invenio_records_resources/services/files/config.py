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
from .results import FileItem, FileList
from .schema import FileSchema, FilesLinks


#
# Configurations
#
class FileServiceConfig(ServiceConfig):
    """File Service configuration."""

    permission_policy_cls = RecordPermissionPolicy
    file_result_item_cls = FileItem
    file_result_list_cls = FileList

    file_schema = FileSchema
    schema_files_links = FilesLinks


class RecordFileServiceConfig(FileServiceConfig, RecordServiceConfig):
    """Service configuration for records with file support."""
