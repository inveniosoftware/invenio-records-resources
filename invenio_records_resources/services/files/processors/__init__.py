# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files processing API."""

from .base import FileProcessor, ProcessorRunner
from .image import ImageMetadataExtractor
from .zip import ZipProcessor

__all__ = (
    "FileProcessor",
    "ImageMetadataExtractor",
    "ProcessorRunner",
    "ZipProcessor",
)
