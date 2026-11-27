# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Tests for opening ZIP archives safely when listing and extracting them."""

import struct
import zipfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from invenio_records_resources.services.errors import (
    FileKeyNotFoundError,
    InvalidFileContentError,
)
from invenio_records_resources.services.files.extractors.zip import ZipExtractor
from invenio_records_resources.services.files.processors.zip import ZipProcessor


class CountingBytesIO(BytesIO):
    """In-memory file counting the bytes read from it."""

    bytes_read = 0

    def read(self, size=-1):
        """Read and count bytes."""
        data = super().read(size)
        self.bytes_read += len(data)
        return data

    def readinto(self, b):
        """Read into a buffer and count bytes."""
        n = super().readinto(b)
        self.bytes_read += n
        return n


def make_zip(count, zip64=False):
    """Create a ZIP archive with ``count`` small files."""
    fp = BytesIO()
    # zipfile only writes the ZIP64 end records for more than 65535 files.
    limit = 0 if zip64 else zipfile.ZIP_FILECOUNT_LIMIT
    with patch("zipfile.ZIP_FILECOUNT_LIMIT", limit):
        with zipfile.ZipFile(fp, "w") as zf:
            for i in range(count):
                zf.writestr(f"folder{i % 7}/file{i:06d}.txt", b"content")
    return fp.getvalue()


def stored_file(data):
    """File record whose storage opens an in-memory copy of ``data``."""
    stream = CountingBytesIO(data)
    file_record = MagicMock(key="archive.zip", metadata={})
    file_record.file.storage.return_value.open.return_value = stream
    file_record.file.file.size = len(data)
    file_record.size = len(data)
    return file_record, stream


def uploaded_file(data):
    """File record as seen by the processor after an upload."""
    stream = CountingBytesIO(data)
    file_record = MagicMock(key="archive.zip", metadata={})
    file_record.open_stream.return_value = stream
    return file_record, stream


@pytest.fixture()
def max_entries(app):
    """Lower the maximum number of entries in a ZIP archive."""
    with patch.dict(app.config, {"RECORDS_RESOURCES_ZIP_MAX_ENTRIES": 5}):
        yield 5


@pytest.mark.parametrize("zip64", [False, True])
@pytest.mark.parametrize("count", [0, 1, 5])
def test_zip_listing_within_limit(app, max_entries, count, zip64):
    """Archives up to the limit are listed as before."""
    file_record, _ = stored_file(make_zip(count, zip64=zip64))

    listing = ZipExtractor().list(file_record)

    assert listing["total"] == count
    assert listing["truncated"] is False


@pytest.mark.parametrize("zip64", [False, True])
def test_zip_listing_too_many_entries(app, max_entries, zip64):
    """Archives over the limit are refused when listing them."""
    file_record, stream = stored_file(make_zip(6, zip64=zip64))

    with pytest.raises(
        InvalidFileContentError, match="Too many files inside the ZIP file."
    ):
        ZipExtractor().list(file_record)
    assert stream.closed


@pytest.mark.parametrize("zip64", [False, True])
def test_zip_open_too_many_entries(app, max_entries, zip64):
    """Archives over the limit are refused when extracting from them."""
    file_record, stream = stored_file(make_zip(6, zip64=zip64))

    with pytest.raises(
        InvalidFileContentError, match="Too many files inside the ZIP file."
    ):
        ZipExtractor().open(file_record, "folder0/file000000.txt")
    assert stream.closed


def test_zip_listing_reads_only_the_end_of_large_archives(app):
    """Archives with many entries are refused reading only their end."""
    data = make_zip(100_000)
    file_record, stream = stored_file(data)

    with pytest.raises(
        InvalidFileContentError, match="Too many files inside the ZIP file."
    ):
        ZipExtractor().list(file_record)

    assert len(data) > 10 * 2**20
    assert stream.bytes_read < 128 * 2**10


def test_zip_listing_not_a_zip(app):
    """Files that are not ZIP archives still raise BadZipFile."""
    file_record, stream = stored_file(b"This is not a ZIP file" * 10)

    with pytest.raises(zipfile.BadZipFile):
        ZipExtractor().list(file_record)
    assert stream.closed


def test_zip_processor_too_many_entries(app, max_entries):
    """The processor saves the error without loading the central directory."""
    data = make_zip(100_000)
    file_record, stream = uploaded_file(data)

    ZipProcessor().process(file_record)

    assert file_record.metadata == {"error": "Too many files inside the ZIP file"}
    assert stream.bytes_read < 128 * 2**10


@pytest.mark.parametrize("zip64", [False, True])
def test_zip_processor_within_limit(app, max_entries, zip64):
    """The processor still records the table of contents position."""
    data = make_zip(5, zip64=zip64)
    file_record, _ = uploaded_file(data)

    ZipProcessor().process(file_record)

    toc_position = file_record.metadata["zip_toc_position"]
    assert data[toc_position : toc_position + 4] == b"PK\x01\x02"


def understate_entries(data, zip64=False):
    """Make the end of central directory record declare a single entry."""
    data = bytearray(data)
    if zip64:
        # entries on this disk and in total, 8 bytes each
        end = data.rfind(b"PK\x06\x06")
        data[end + 24 : end + 40] = struct.pack("<QQ", 1, 1)
    else:
        # entries on this disk and in total, 2 bytes each
        end = data.rfind(b"PK\x05\x06")
        data[end + 8 : end + 12] = struct.pack("<HH", 1, 1)
    return bytes(data)


@pytest.mark.parametrize("zip64", [False, True])
def test_zip_understated_entries(app, max_entries, zip64):
    """An understated count of entries is caught after parsing."""
    data = understate_entries(make_zip(6, zip64=zip64), zip64=zip64)
    file_record, stream = stored_file(data)
    with pytest.raises(
        InvalidFileContentError, match="Too many files inside the ZIP file."
    ):
        ZipExtractor().list(file_record)
    assert stream.closed

    file_record, stream = stored_file(data)
    with pytest.raises(
        InvalidFileContentError, match="Too many files inside the ZIP file."
    ):
        ZipExtractor().open(file_record, "folder0/file000000.txt")
    assert stream.closed

    file_record, stream = stored_file(data)
    with pytest.raises(
        InvalidFileContentError, match="Too many files inside the ZIP file."
    ):
        ZipExtractor()._open_zip(file_record)
    assert stream.closed

    file_record, _ = uploaded_file(data)
    ZipProcessor().process(file_record)
    assert file_record.metadata == {"error": "Too many files inside the ZIP file"}


def test_zip_central_directory_too_large(app):
    """A large central directory is refused before reading it."""
    # more than 65535 entries: zipfile writes the ZIP64 end records
    data = understate_entries(make_zip(100_000), zip64=True)
    message = "The table of contents of the ZIP file is too large"

    file_record, stream = stored_file(data)
    with pytest.raises(InvalidFileContentError, match=message):
        ZipExtractor().list(file_record)
    assert stream.closed
    assert stream.bytes_read < 128 * 2**10

    file_record, stream = uploaded_file(data)
    ZipProcessor().process(file_record)
    assert file_record.metadata == {"error": message}
    assert stream.bytes_read < 128 * 2**10


@pytest.mark.parametrize("with_toc", [False, True])
def test_zip_read_content_after_opening(app, max_entries, with_toc):
    """Entries are read, with and without a cached table of contents."""
    content = b"0123456789" * 100_000
    fp = BytesIO()
    with zipfile.ZipFile(fp, "w") as zf:
        zf.writestr("big.txt", content)
        zf.comment = b"x" * 65535
    data = fp.getvalue()

    file_record, _ = stored_file(data)
    if with_toc:
        file_record.metadata = {"zip_toc_position": data.rfind(b"PK\x01\x02")}

    with ZipExtractor().open(file_record, "big.txt") as member:
        assert member.read() == content


def test_zip_open_member_size(app):
    """The size of an extracted member is its uncompressed size."""
    file_record, _ = stored_file(make_zip(1))

    with ZipExtractor().open(file_record, "folder0/file000000.txt") as member:
        assert member.size == len(b"content")


def test_zip_open_missing_path_closes_stream(app):
    """The stored file is closed when the path is not in the archive."""
    file_record, stream = stored_file(make_zip(1))

    with pytest.raises(FileKeyNotFoundError):
        ZipExtractor().open(file_record, "missing.txt")
    assert stream.closed


@pytest.mark.parametrize("count, truncated", [(4, False), (5, False), (6, True)])
def test_zip_listing_truncated(app, count, truncated):
    """The listing is flagged as truncated only when entries are left out."""
    file_record, _ = stored_file(make_zip(count))
    config = {"RECORDS_RESOURCES_ZIP_MAX_LISTING_ENTRIES": 5}
    with patch.dict(app.config, config):
        listing = ZipExtractor().list(file_record)

    assert listing["total"] == min(count, 5)
    assert listing["truncated"] is truncated
