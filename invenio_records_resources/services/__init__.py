# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""High-level API for wokring with records, files, pids and search."""

from .base import Service, ServiceConfig
from .files import FileMetadataService, FileMetadataServiceConfig, \
    FileService, FileServiceConfig
from .records import DataSchema, MarshmallowDataSchema, RecordService, \
    RecordServiceConfig

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
