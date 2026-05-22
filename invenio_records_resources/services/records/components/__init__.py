# SPDX-FileCopyrightText: 2020-2023 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-License-Identifier: MIT

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
