# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""High-level API for wokring with records, files, pids and search."""

from .data_validator import DataValidator, MarshmallowDataValidator
from .file_metadata_service import FileMetadataService, \
    FileMetadataServiceConfig
from .file_service import FileService, FileServiceConfig
from .record_service import RecordService, RecordServiceConfig

__all__ = (
    "DataValidator",
    "FileMetadataService",
    "FileMetadataServiceConfig",
    "FileService",
    "FileServiceConfig",
    "MarshmallowDataValidator",
    "RecordService",
    "RecordServiceConfig",
)
