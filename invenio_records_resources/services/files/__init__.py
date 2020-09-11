# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Base Service API."""

from .config import FileServiceConfig, FileMetadataServiceConfig
from .service import FileService, FileMetadataService

__all__ = (
    'FileMetadataService',
    'FileMetadataServiceConfig',
    'FileService',
    'FileServiceConfig',
)
