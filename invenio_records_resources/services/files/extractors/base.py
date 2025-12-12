# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Base classes for file extractors."""

import io
from abc import ABC, abstractmethod


class FileExtractor(ABC):
    """Base class for file extractors."""

    @abstractmethod
    def can_process(self, file_record):
        """
        Determine if this extractor can process a given file record.

        :param file_record: FileRecord object to be processed
        """

    @abstractmethod
    def list(self, file_record):
        """Return a listing of the file.

        :param file_record: FileRecord object to be listed
        :returns: dict

        example: {
            "entries": [ // all entries inside the container
                {
                    "key": "texts_folder/test1.txt",
                    "size": 12,
                    "compressed_size": 14,
                    "mimetype": "text/plain",
                    "checksum": "crc:2962613731",
                    "links" {"content": ".../api/records/abc123-yz89/files/demo.zip/container/texts_folder/test1.txt"} // links are added automatically by service and not returned by the extractor itself
                },
                {
                    "key": "texts_folder/texts_subfolder/test2.txt",
                    "size": 12,
                    "compressed_size": 14,
                    "mimetype": "text/plain",
                    "checksum": "crc:2962613731",
                    "links" {"content": ".../api/records/abc123-yz89/files/demo.zip/container/texts_folder/texts_subfolder/test2.txt"} // links are added automatically by service and not returned by the extractor itself
                }
            ],
            "folders": [ // all folders inside the container
                {
                  "key": "texts_folder",
                  "links": { // links are added automatically by service and not returned by the extractor itself
                    "content": ".../api/records/abc123-yz89/files/demo.zip/container/texts_folder"
                  },
                  "entries": [ // paths of direct children (files or folders) of the container folder
                    "texts_folder/test1.txt",
                    "texts_folder/texts_subfolder"
                  ]
                },
                {
                  "key": "texts_folder/texts_subfolder"
                  "links": {
                    "content": ".../api/records/abc123-yz89/files/demo.zip/container/texts_folder/texts_subfolder"
                  },
                  "entries": [ // paths of direct children (files or folders) of the container folder
                    "texts_subfolder/test2.txt"]
                }
            ],
            "total": 2,  // total number of entries
            "truncated": false // true if the listing was truncated (e.g., too many entries)
        }
        """

    @abstractmethod
    def open(self, file_record, path) -> io.IOBase:
        """Open a specific file from the file record."""
        pass
