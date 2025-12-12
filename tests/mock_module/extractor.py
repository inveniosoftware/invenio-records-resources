# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""File service dummy extractors."""

from invenio_records_resources.services.files.extractors.base import FileExtractor


class DummyFileExtractor(FileExtractor):
    """A dummy file extractor for testing purposes."""

    def can_process(self, file_record):
        """Determine if this extractor can process a given file record."""
        return file_record.key.endswith(".txt")

    def list(self, file_record):
        """List the contents of a given file record."""
        return {
            "children": {
                "dummy.txt": {
                    "key": "dummy.txt",
                    "type": "file",
                    "size": "123456790",
                    "id": "dummy.txt",
                }
            },
            "total": 1,
            "truncated": False,
        }

    def extract(self, file_record, path):
        """Extract a specific file or directory from the file record."""

        class DummySendFile:
            """A dummy send file protocol implementation."""

            def send_file(self):
                """Simulate sending a file."""
                return f"Sending {path} from {file_record.key}"

        return DummySendFile()

    def open(self, file_record, path):
        """Open a specific file from the file record."""
        from io import StringIO

        # Simulate opening a file by returning a StringIO object
        return StringIO(f"Contents of {path} from {file_record.key}")
