# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020-2025 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Mock test module."""

from invenio_records_resources.resources import FileResource, RecordResource
from invenio_records_resources.services import FileService, RecordService
from tests.mock_module.config import (
    FileServiceConfig,
    ServiceConfig,
    ServiceWithFilesConfig,
)
from tests.mock_module.resource import (
    CustomDisabledUploadFileResourceConfig,
    CustomFileResourceConfig,
    CustomRecordResourceConfig,
)

service_for_records = RecordService(ServiceConfig)
service_for_records_w_files = RecordService(ServiceWithFilesConfig)
service_for_files = FileService(FileServiceConfig)


def create_mocks_bp(app):
    """Create mocks Blueprint."""
    service = service_for_records
    resource = RecordResource(CustomRecordResourceConfig, service)
    return resource.as_blueprint()


def create_mocks_w_files_bp(app):
    """Create mocks with files Blueprint.

    This blueprint and the one above cannot be registered together
    as they use the same blueprint name. This is in keeping with
    pre-existing tests.
    """
    service = service_for_records_w_files
    resource = RecordResource(CustomRecordResourceConfig, service)
    return resource.as_blueprint()


def create_mocks_files_bp(app):
    """Create mocks files Blueprint."""
    service = service_for_files
    resource = FileResource(CustomFileResourceConfig, service)
    return resource.as_blueprint()


def create_mocks_files_disabled_upload_bp(app):
    """Create mocks disabled files Blueprint."""
    service = service_for_files
    resource = FileResource(CustomDisabledUploadFileResourceConfig, service)
    return resource.as_blueprint()
