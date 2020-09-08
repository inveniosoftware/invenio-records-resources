# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""High-level API for wokring with records, files, pids and search."""

from .data_schema import DataSchema, MarshmallowDataSchema
from .file import FileService, FileServiceConfig
from .file_metadata import FileMetadataService, FileMetadataServiceConfig
from .record import RecordService, RecordServiceConfig
from .service import Service, ServiceConfig

__all__ = (
    "DataSchema",
    "FileMetadataService",
    "FileMetadataServiceConfig",
    "FileService",
    "FileServiceConfig",
    "MarshmallowDataSchema",
    "RecordService",
    "RecordServiceConfig",
    "Service",
    "ServiceConfig",
)
