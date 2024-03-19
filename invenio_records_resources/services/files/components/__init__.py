# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2024 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files service components."""

from .base import FileServiceComponent
from .content import FileContentComponent
from .filetype import FileTypeDetectionComponent
from .metadata import FileMetadataComponent
from .processor import FileProcessorComponent

__all__ = (
    "FileContentComponent",
    "FileMetadataComponent",
    "FileProcessorComponent",
    "FileServiceComponent",
    "FileTypeDetectionComponent",
)
