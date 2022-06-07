# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Image metadata extractor."""

import os

import pkg_resources

from .base import FileProcessor

try:
    pkg_resources.get_distribution("wand")
    from wand.image import Image

    HAS_IMAGEMAGICK = True
except pkg_resources.DistributionNotFound:
    # Python module not installed
    HAS_IMAGEMAGICK = False
except ImportError:
    # ImageMagick notinstalled
    HAS_IMAGEMAGICK = False


class ImageMetadataExtractor(FileProcessor):
    """Basic image metadata extractor."""

    def can_process(self, file_record):
        """Images can be processed."""
        if HAS_IMAGEMAGICK:
            ext = self.file_extension(file_record).lower()
            return ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]
        return False

    def process(self, file_record):
        """Process the file record.

        Security: Do not execute ImageMagick inside an HTTP request. Always
        execute via e.g. a Celery task. See
        https://docs.wand-py.org/en/0.6.6/guide/security.html
        """
        # TODO: gracefully deal with errors.
        # TODO: security
        width = -1
        height = -1

        ext = self.file_extension(file_record)[1:]

        with file_record.open_stream("rb") as fp:
            with Image.ping(file=fp, format=ext) as img:
                width = img.width
                height = img.height

        if width > 0 and height > 0:
            file_record.metadata.update({"width": width, "height": height})
