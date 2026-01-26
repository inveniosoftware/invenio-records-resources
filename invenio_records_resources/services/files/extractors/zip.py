# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zip file extractor/listing using cached TOC for efficient extraction."""

import base64
import json
import mimetypes
import os
import zipfile
from io import RawIOBase
from flask import Response, current_app, stream_with_context
from pathlib import PurePosixPath
from zipstream import ZIP_DEFLATED, ZipStream

from invenio_records_resources.services.files.extractors.base import FileExtractor
from .reply_stream import ReplyStream


def _get_mimetype(filename):
    return mimetypes.guess_type(PurePosixPath(filename).parts[-1])[0] or "application/octet-stream"

class ZipFileProxy(RawIOBase):
    def __init__(self, zip_file, file_info, zip_proxy):
        self._zip_file = zip_file
        self._file_info = file_info
        self._zip_proxy = zip_proxy

    def readinto(self, b):
        return self._zip_file.readinto(b)

    def close(self):
        self._zip_file.close()
        self._zip_proxy.close()

    @property
    def mimetype(self):
        return _get_mimetype(self._file_info.filename)

    @property
    def size(self):
        return self._file_info.size

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def seek(self, *args):
        return self._zip_file.seek(*args)

    def tell(self):
        return self._zip_file.tell()


class ZipProxy:

    def __init__(self, file_record):
        f = file_record.file.storage().open("rb")
        metadata = file_record.metadata or {}
        toc_position = metadata.get("zip_toc_position", None)
        file_size = file_record.file.file.size
        # Make sure that malicious toc position doesn't exhaust memory.
        if toc_position and file_size - toc_position < current_app.config["RECORDS_RESOURCES_ZIP_MAX_HEADER_SIZE"]:
            reply_stream = ReplyStream(f, buffer_pos=toc_position, file_size=file_record.file.file.size)
        else:
            reply_stream = f

        self.reply_stream = reply_stream
        self.zip_file = zipfile.ZipFile(reply_stream, "r")
        self.infolist = list(self.zip_file.infolist())

    def close(self):
        self.reply_stream.close()

    def open(self, path):
        open_zip_file = self.zip_file.open(path)
        file_info = next(i for i in self.infolist if i.filename == path)
        return ZipFileProxy(open_zip_file, file_info, self)


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class ZipExtractor(FileExtractor):
    """
    Extractor for ZIP files that uses the pre-built table of contents for efficient extraction.

    This extractor leverages the cached TOC created by ZipProcessor to:
    - Quickly locate files without scanning the entire ZIP
    - Stream individual files without loading them fully into memory
    - Create directory ZIPs on-the-fly without buffering in memory
    """

    def can_process(self, file_record):
        """Determine if this extractor can process a given file record."""
        print("can_process", os.path.splitext(file_record.key)[-1].lower(), current_app.config["RECORDS_RESOURCES_ZIP_FORMATS"])
        return (
                os.path.splitext(file_record.key)[-1].lower()
                in current_app.config["RECORDS_RESOURCES_ZIP_FORMATS"]
        )


    def _open_zip(self, file_record):
        f = file_record.file.storage().open("rb")
        metadata = file_record.metadata or {}
        toc_position = metadata.get("zip_toc_position", None)
        if toc_position:
            reply_stream = ReplyStream(f, buffer_pos=toc_position, file_size=file_record.size)
        else:
            reply_stream = f
        return reply_stream, zipfile.ZipFile(reply_stream, "r")

    def list(self, file_record):
        """Return the cached table of contents for the ZIP file."""
        truncated = False
        total_entries = 0
        entries = []
        max_entries = current_app.config["RECORDS_RESOURCES_ZIP_MAX_ENTRIES"]

        with ZipProxy(file_record) as zip_file:

            # Iterate through all entries in the ZIP's central directory
            # Recording Stream will capture byte range accessed
            for info in zip_file.infolist:
                if info.is_dir():
                    continue
                entries.append({
                    "key": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "mimetype": _get_mimetype(info.filename),
                    "crc": info.CRC,
                })
                total_entries += 1
                if max_entries and total_entries >= max_entries:
                    truncated = True
                    break
        return {"entries": entries, "truncated": truncated, "total": total_entries}

    def open(self, file_record, path):
        """Open a specific file from the file record.

        Return a readable stream that remains open until the caller closes it.
        """
        return ZipProxy(file_record).open(path)
