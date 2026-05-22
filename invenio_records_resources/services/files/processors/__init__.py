# SPDX-FileCopyrightText: 2021 CERN.
# SPDX-License-Identifier: MIT

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
