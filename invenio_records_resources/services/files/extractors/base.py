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

from invenio_records_resources.records.api import FileRecord


class SendFileProtocol(Protocol):
    """Protocol for send_file method."""

    def send_file(self) -> None:
        """Protocol for send_file method."""
        ...


class FileExtractor:
    """Base class for file extractors."""

    @staticmethod
    def file_extension(file_record):
        """Return the extension of the file."""
        return os.path.splitext(file_record.key)[-1].lower()

    def can_process(self, file_record: FileRecord) -> bool:
        """Determine if this extractor can process a given file record."""

    def list(self, file_record: FileRecord) -> list[dict]:
        """Return a listing of the file."""

    def extract(self, file_record: FileRecord, path: str) -> SendFileProtocol:
        """Extract a specific file or directory from the file record."""

    def open(self, file_record, path) -> io.IOBase:
        """Open a specific file from the file record."""
        pass
