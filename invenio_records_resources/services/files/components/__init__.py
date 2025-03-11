# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files service components."""

from .base import FileServiceComponent
from .content import FileContentComponent
from .metadata import FileMetadataComponent
from .multipart import FileMultipartContentComponent
from .processor import FileProcessorComponent

__all__ = (
    "FileContentComponent",
    "FileMetadataComponent",
    "FileProcessorComponent",
    "FileServiceComponent",
    "FileMultipartContentComponent",
)
