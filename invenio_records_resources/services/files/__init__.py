# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files Service API."""

from .config import FileServiceConfig, RecordFileServiceConfig
from .service import FileServiceMixin, RecordFileService

__all__ = (
    'FileServiceConfig',
    'FileServiceMixin',
    'RecordFileServiceConfig',
    'RecordFileService',
)
