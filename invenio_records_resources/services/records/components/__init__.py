# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2023 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service components module."""

from .base import ServiceComponent
from .data import DataComponent
from .files import BaseRecordFilesComponent, FilesComponent
from .metadata import MetadataComponent
from .relations import ChangeNotificationsComponent, RelationsComponent

__all__ = (
    "ServiceComponent",
    "DataComponent",
    "MetadataComponent",
    "RelationsComponent",
    "ChangeNotificationsComponent",
    "BaseRecordFilesComponent",
    "FilesComponent",
)
