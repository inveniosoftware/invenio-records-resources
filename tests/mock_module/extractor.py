# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""File service dummy extractors."""

from io import StringIO

from invenio_records_resources.services.files.extractors.base import FileExtractor


class DummyFileExtractor(FileExtractor):
    """A dummy file extractor for testing purposes."""

    def can_process(self, file_record):
        """Determine if this extractor can process a given file record."""
        return file_record.key.endswith(".txt")

    def list(self, file_record):
        """List the contents of a given file record."""
        return {
            "entries": [
                {
                    "key": "dummy.txt",
                    "size": 123456790,
                }
            ],
            "total": 1,
            "truncated": False,
        }

    def open(self, file_record, path):
        """Open a specific file from the file record."""
        # Simulate opening a file by returning a StringIO object

        io_contents = StringIO(f"Contents of {path} from {file_record.key}")
        io_contents.mimetype = "text/plain"

        return io_contents
