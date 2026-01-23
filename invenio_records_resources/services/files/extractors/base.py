# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Base classes for file extractors."""

import io
import os
from typing import Protocol
from abc import ABC, abstractmethod


class FileExtractor(ABC):
    """Base class for file extractors."""

    @abstractmethod
    def can_process(self, file_record):
        """Determine if this extractor can process a given file record.

        :param file_record: FileRecord object to be processed"""

    @abstractmethod
    def list(self, file_record):
        """Return a listing of the file.

        :param file_record: FileRecord object to be listed
        :returns: dict

        example: {
            "entries": [
                {
                    "key": "test_zip/test1.txt",
                    "size": 12,
                    "compressed_size": 14,
                    "mimetype": "text/plain",
                    "checksum": "crc:2962613731",
                }
            ],
            "total": 1,  // total number of entries
            "truncated": false, // true if the listing was truncated (e.g., too many entries)
        }
        """

    @abstractmethod
    def open(self, file_record, path) -> io.IOBase:
        """Open a specific file from the file record."""
        pass
