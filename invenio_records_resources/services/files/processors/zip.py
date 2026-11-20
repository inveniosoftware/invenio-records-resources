# SPDX-FileCopyrightText: 2025 CESNET i.a.l.e.
# SPDX-FileCopyrightText: 2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

"""ZIP file processor that builds and caches a table of contents for efficient extraction."""

import os
import zipfile

from flask import current_app

from ...errors import InvalidZipException
from .base import FileProcessor


def check_zip_entries_count(fp):
    """Raise if the ZIP archive has more entries than allowed.

    Only the end of central directory record at the end of the file is read,
    so an archive with millions of entries is rejected before ``zipfile``
    loads its whole central directory in memory.
    """
    endrec = zipfile._EndRecData(fp)
    if not endrec:
        raise zipfile.BadZipFile("File is not a zip file")
    entries = endrec[zipfile._ECD_ENTRIES_TOTAL]
    max_files = current_app.config["RECORDS_RESOURCES_ZIP_MAX_ENTRIES"]
    if entries > max_files:
        raise InvalidZipException("Too many files inside the ZIP file")


class ZipProcessor(FileProcessor):
    """Processor for ZIP files that verifies the content of zip and stores position of table of contents to file metadata."""

    def can_process(self, file_record):
        """Determine if this processor can process a given file record."""
        return (
            os.path.splitext(file_record.key)[-1].lower()
            in current_app.config["RECORDS_RESOURCES_ZIP_FORMATS"]
        )

    def process(self, file_record):
        """Process the uploaded ZIP file."""
        metadata = file_record.metadata or {}
        try:
            toc_position = self._check_zip_file(file_record)
            metadata.update({"zip_toc_position": toc_position})
        except (InvalidZipException, zipfile.BadZipFile) as e:
            metadata.update({"error": str(e)})

        file_record.metadata = metadata

    def _check_zip_file(self, file_record):
        """Check the contents of zip file and return the position of table of contents."""
        # Open the ZIP file and wrap it in RecordingStream to track byte ranges
        with file_record.open_stream("rb") as fp:
            check_zip_entries_count(fp)
            recorded_stream = RecordingStream(fp)
            with zipfile.ZipFile(recorded_stream) as zf:
                # Iterate through all entries in the ZIP's central directory
                # Recording Stream will capture byte range accessed
                infolist = zf.infolist()
                toc_position = recorded_stream.toc_position
                self._check_infolist(infolist)
        return toc_position

    def _check_infolist(self, infolist):
        # max files count check
        max_files = current_app.config["RECORDS_RESOURCES_ZIP_MAX_ENTRIES"]
        if len(infolist) > max_files:
            raise InvalidZipException("Too many files inside the ZIP file")

        total_uncompressed = 0
        for info in infolist:

            #: path traversal check
            name = info.filename
            # normalize separators
            name = name.replace("\\", "/")
            if name.startswith("/") or name.startswith("../") or "/../" in name:
                raise InvalidZipException(
                    f"Path traversal in ZIP entry: {info.filename}"
                )

            # ratio check
            if info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > current_app.config["RECORDS_RESOURCES_ZIP_MAX_RATIO"]:
                    raise InvalidZipException(
                        f"Suspicious compression ratio {ratio:.1f} in {info.filename}"
                    )

            #: total_uncompressed_check
            total_uncompressed += info.file_size
            if (
                total_uncompressed
                > current_app.config["RECORDS_RESOURCES_ZIP_MAX_TOTAL_UNCOMPRESSED"]
            ):
                raise InvalidZipException("Total uncompressed size limit exceeded")


class RecordingStream:
    """A wrapper around a file stream that records the byte ranges accessed."""

    def __init__(self, fp):
        """Initialize the RecordingStream with the given file-like object."""
        self.fp = fp
        self.toc_position = None

    def seek(self, offset, whence=os.SEEK_SET):
        """Seek to a position and record the byte offset.

        This method tracks the minimum and maximum byte offsets accessed.
        """
        self.fp.seek(offset, whence)

        actual_pos = self.fp.tell()
        if self.toc_position is None or actual_pos < self.toc_position:
            self.toc_position = actual_pos

    def tell(self):
        """Delegate tell to the underlying stream."""
        return self.fp.tell()

    def read(self, size=-1):
        """Delegate read to the underlying stream."""
        return self.fp.read(size)
