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
        """Create a proxy around an opened ZIP member.

        Args:
            zip_file: The file-like object returned by `zipfile.ZipFile.open()`.
            file_info: The corresponding `zipfile.ZipInfo` entry.
            zip_proxy: The owning `ZipProxy` instance to close when done.
        """
        self._zip_file = zip_file
        self._file_info = file_info
        self._zip_proxy = zip_proxy

    def readinto(self, b):
        """Read bytes from the ZIP member into buffer ``b``.

        Args:
            b: A writable, buffer-protocol object (e.g., `bytearray`).

        Returns:
            Number of bytes read.
        """
        return self._zip_file.readinto(b)

    def close(self):
        """Close both the ZIP member stream and the parent ZIP proxy.

        This ensures the ZIP container stream is released even if the caller only
        holds on to the member stream.
        """
        self._zip_file.close()
        self._zip_proxy.close()

    @property
    def mimetype(self):
        """Best-effort MIME type inferred from the member filename."""
        return _get_mimetype(self._file_info.filename)

    @property
    def size(self):
        """Uncompressed size of this ZIP member in bytes."""
        return self._file_info.size

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def seek(self, *args):
        """Seek within the ZIP member stream.

        Delegates to the underlying zip member file object.
        """
        return self._zip_file.seek(*args)

    def tell(self):
        """Return current position within the ZIP member stream."""
        return self._zip_file.tell()


class ZipProxy:
    """Open and manage a ZIP archive stream with optional TOC-aware optimization.

    `ZipProxy` is responsible for:
      - Opening the underlying stored file (the ZIP container)
      - Optionally wrapping it in `ReplyStream` so reads of the ZIP central directory
        (table of contents / TOC) come from memory, reducing I/O and enabling
        efficient listing/opening
      - Creating a `zipfile.ZipFile` and caching its `infolist()` for quick lookups

    The proxy is a context manager and should be closed to release file handles.
    """

    def __init__(self, file_record):
        """Create a ZIP proxy for a stored file record.

        Args:
            file_record: Storage-backed record holding a ZIP file and metadata.
                Expected to provide:
                - `file_record.file.storage().open("rb")` to open the bytes
                - `file_record.metadata` for optional TOC offset (zip_toc_position)
                - `file_record.file.file.size` for total byte size (used for bounds)

        Notes:
            If `zip_toc_position` is present and passes a safety check, the code
            caches the region from that position to EOF using `ReplyStream`.
            This defends against malicious offsets that would otherwise cause
            excessive memory allocation.
        """
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
        """Close the underlying reply stream.

        Note:
            Closing `reply_stream` should release the underlying file handle.
            (The `zipfile.ZipFile` object does not always close the underlying
            file-like object unless you call `ZipFile.close()` explicitly.)
        """
        self.reply_stream.close()

    def open(self, path):
        """Open a member file inside the ZIP by its path/name.

        Args:
            path: Member filename as stored in the ZIP (exact match).

        Returns:
            A `ZipFileProxy` stream for the requested member. Closing the returned
            stream will also close this `ZipProxy`.
        """
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
        return (
                os.path.splitext(file_record.key)[-1].lower()
                in current_app.config["RECORDS_RESOURCES_ZIP_FORMATS"]
        )


    def _open_zip(self, file_record):
        """Open the underlying ZIP stream and build a `zipfile.ZipFile`.

        Args:
            file_record: Storage-backed record holding a ZIP file and metadata.

        Returns:
            A tuple of `(reply_stream, zipfile_obj)` where:
              - `reply_stream` is either the raw storage stream or a `ReplyStream`
                wrapper if a TOC position is available.
              - `zipfile_obj` is an instance of `zipfile.ZipFile` opened for reading.

        Notes:
            This helper does not apply the additional "max header size" safety check
            used by `ZipProxy` in the code above; it trusts the presence of
            `zip_toc_position` and wraps immediately when provided.
        """
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
        """Open a specific member file from the ZIP as a stream.

        Args:
            file_record: Record describing the stored ZIP file.
            path: Member filename as stored in the ZIP (exact match).

        Returns:
            A readable stream (`ZipFileProxy`) that remains open until the caller closes it.

        Notes:
            The returned stream owns the underlying ZIP resources; closing it will
            also close the associated `ZipProxy`.
        """
        return ZipProxy(file_record).open(path)
