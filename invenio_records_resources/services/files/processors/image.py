# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Image metadata extractor."""

import pkg_resources
from flask import current_app

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

try:
    import pyvips

    HAS_VIPS = True
except ModuleNotFoundError:
    # Python module pyvips not installed
    HAS_VIPS = False
except OSError:
    # Underlying library libvips not installed
    HAS_VIPS = False


class ImageMetadataExtractor(FileProcessor):
    """Basic image metadata extractor."""

    def can_process(self, file_record):
        """Images can be processed."""
        if HAS_IMAGEMAGICK or HAS_VIPS:
            ext = self.file_extension(file_record).lower()
            return ext in current_app.config["RECORDS_RESOURCES_IMAGE_FORMATS"]
        return False

    def _process_wand(self, file_record):
        """Process the file record using Wand.

        Warning: Wand (and ImageMagick) actually reads the entire file in memory to
        extract the image metadata.

        Security: Do not execute ImageMagick inside an HTTP request. Always
        execute via e.g. a Celery task. See
        https://docs.wand-py.org/en/0.6.6/guide/security.html
        """
        width = height = -1
        with file_record.open_stream("rb") as fp:
            with Image.ping(file=fp) as img:
                # Get image or first frame of sequence
                img_or_seq = img if not len(img.sequence) else img.sequence[0]
                width = img_or_seq.width
                height = img_or_seq.height
        return width, height

    def _process_vips(self, file_record):
        """Process the file record using pyvips."""
        width = height = -1
        with file_record.open_stream("rb") as fp:

            def _seek_handler(offset, whence):
                fp.seek(offset, whence)
                return fp.tell()

            source = pyvips.SourceCustom()
            source.on_read(fp.read)
            source.on_seek(_seek_handler)

            image = pyvips.Image.new_from_source(source, "", access="sequential")
            width = image.width
            height = image.height
        return width, height

    def process(self, file_record):
        """Process the file record."""
        width = height = -1

        # Prefer VIPS if available
        if HAS_VIPS:
            width, height = self._process_vips(file_record)
        elif HAS_IMAGEMAGICK:
            width, height = self._process_wand(file_record)

        if width > 0 and height > 0:
            metadata = file_record.metadata or {}
            metadata.update({"width": width, "height": height})
            file_record.metadata = metadata
