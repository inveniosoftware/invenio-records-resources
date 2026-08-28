import io
import zipfile
from os.path import dirname, join
from unittest.mock import MagicMock

import pytest
from werkzeug.exceptions import RequestedRangeNotSatisfiable

from invenio_records_resources.services.errors import InvalidFileContentError
from invenio_records_resources.services.files.components import processor
from invenio_records_resources.services.files.extractors.zip import ZipFileProxy
from invenio_records_resources.tasks import extract_file_metadata


@pytest.fixture()
def record_with_zip(
    file_service, location, example_record, identity_simple, zip_fp, monkeypatch
):
    """Image metadata extraction."""
    # Patch celery task
    task = MagicMock()
    monkeypatch.setattr(processor, "extract_file_metadata", task)

    recid = example_record["id"]

    # Upload file
    file_service.init_files(identity_simple, recid, [{"key": "testzip.zip"}])
    file_service.set_file_content(identity_simple, recid, "testzip.zip", zip_fp)

    # Commit (should send celery task)
    assert not task.apply_async.called
    file_service.commit_file(identity_simple, recid, "testzip.zip")
    assert task.apply_async.called

    # Call task manually
    extract_file_metadata(*task.apply_async.call_args[1]["args"])

    return example_record


def test_zip_listing(identity_simple, file_service, record_with_zip):
    recid = record_with_zip["id"]
    listing = file_service.list_container(identity_simple, recid, "testzip.zip")
    entries = list(listing.entries)
    assert entries == [
        {
            "key": "a.txt",
            "size": 24,
            "compressed_size": 24,
            "mimetype": "text/plain",
            "crc": 3057564182,
            "links": {
                "content": f"https://127.0.0.1:5000/api/mocks/{recid}/files/testzip.zip/container/a.txt"
            },
        },
        {
            "key": "b.txt",
            "size": 24,
            "compressed_size": 24,
            "mimetype": "text/plain",
            "crc": 3057564182,
            "links": {
                "content": f"https://127.0.0.1:5000/api/mocks/{recid}/files/testzip.zip/container/b.txt"
            },
        },
        {
            "key": "c.txt",
            "size": 24,
            "compressed_size": 24,
            "mimetype": "text/plain",
            "crc": 3057564182,
            "links": {
                "content": f"https://127.0.0.1:5000/api/mocks/{recid}/files/testzip.zip/container/c.txt"
            },
        },
        {
            "key": "d.txt",
            "size": 24,
            "compressed_size": 24,
            "mimetype": "text/plain",
            "crc": 3057564182,
            "links": {
                "content": f"https://127.0.0.1:5000/api/mocks/{recid}/files/testzip.zip/container/d.txt"
            },
        },
    ]


def test_read_zip(identity_simple, file_service, record_with_zip):
    recid = record_with_zip["id"]
    with file_service.open_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    ) as f:
        data = f.read()
        assert data == b"Hello world from a.txt.\n"


def test_zip_extraction(identity_simple, file_service, record_with_zip):
    recid = record_with_zip["id"]
    extracted = file_service.extract_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    )
    extracted_data = extracted.send_file()
    # For direct_passthrough responses, consume the iterator to get data
    content = b"".join(extracted_data.iter_encoded())
    assert content == b"Hello world from a.txt.\n"


def test_zipfileproxy_size_property(identity_simple, file_service, record_with_zip):
    """Test that ZipFileProxy.size returns the correct file_size.

    This is a regression test for the bug where ZipFileProxy.size used
    self._file_info.size instead of self._file_info.file_size, causing
    AttributeError since ZipInfo has no 'size' attribute.
    """
    recid = record_with_zip["id"]

    # Open a file from the container
    stream = file_service.open_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    )

    # Verify the stream is a ZipFileProxy with working size property
    assert isinstance(stream, ZipFileProxy)

    # The size property should return the correct uncompressed size
    # (not raise AttributeError)
    assert stream.size == 24

    # Verify Content-Length would be set correctly in send_file response
    extracted = file_service.extract_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    )
    response = extracted.send_file()
    assert response.headers.get("Content-Length") == "24"


def test_zipfileproxy_io_methods(identity_simple, file_service, record_with_zip):
    """Test that ZipFileProxy correctly reports its IO capabilities.

    This is a regression test for the issue where ZipFileProxy inherited
    default IOBase methods that reported the stream as non-seekable and
    non-readable, even though it implements seek(), tell(), and readinto().
    """
    recid = record_with_zip["id"]

    # Open a file from the container
    stream = file_service.open_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    )

    # Verify the stream is a ZipFileProxy
    assert isinstance(stream, ZipFileProxy)

    # Test readable() - should return True since we can read from ZIP members
    assert stream.readable() is True

    # Test seekable() - should return True since ZipExtFile supports seeking
    assert stream.seekable() is True

    # Test writable() - should return False as we only support reading
    assert stream.writable() is False

    # Also verify that seek() and tell() work correctly
    initial_pos = stream.tell()
    assert initial_pos == 0

    # Read some data
    data = stream.read(10)
    assert len(data) == 10

    # Verify position advanced
    pos_after_read = stream.tell()
    assert pos_after_read == 10

    # Seek back to beginning
    stream.seek(0)
    assert stream.tell() == 0

    # Seek to offset
    stream.seek(5)
    assert stream.tell() == 5

    # Close the stream
    stream.close()


def test_zipfileproxy_io_methods_deflated(
    identity_simple, file_service, record_with_zip
):
    """Test IO methods work correctly for both STORED and DEFLATED compression.

    The testzip.zip fixture uses ZIP_STORED compression. This test verifies
    that the IO methods work correctly regardless of compression type.
    """
    # Create a ZIP with DEFLATED compression
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("deflated.txt", "Compressed content")

    # Manually create a ZipFileProxy to test with DEFLATED
    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        info = zf.infolist()[0]
        opened = zf.open("deflated.txt")

        class FakeProxy:
            def close(self):
                pass

        proxy = ZipFileProxy(opened, info, FakeProxy())

        # All IO methods should work the same for DEFLATED
        assert proxy.readable() is True
        assert proxy.seekable() is True
        assert proxy.writable() is False

        # Verify size is correct
        assert proxy.size == 18

        proxy.close()


def test_container_item_as_attachment(identity_simple, file_service, record_with_zip):
    """Test that as_attachment parameter controls Content-Disposition header.

    This is a regression test for the bug where Content-Disposition was always
    set to 'attachment' regardless of the as_attachment parameter value.
    """
    recid = record_with_zip["id"]

    # Test with as_attachment=True (default behavior)
    extracted = file_service.extract_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    )
    response = extracted.send_file(as_attachment=True)
    # Note: send_stream() uses werkzeug's Content-Disposition building which
    # doesn't add unnecessary quotes around simple ASCII filenames
    assert "attachment; filename=a.txt" in response.headers.get("Content-Disposition")

    # Test with as_attachment=False (should use 'inline' without filename)
    extracted = file_service.extract_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    )
    response = extracted.send_file(as_attachment=False)
    # When as_attachment=False, send_stream() sets just 'inline' without filename
    assert response.headers.get("Content-Disposition") == "inline"


def test_container_item_range_requests_disabled(
    app, identity_simple, file_service, record_with_zip, monkeypatch
):
    """Test that Range requests return full response when disabled (default)."""
    recid = record_with_zip["id"]

    # Ensure Range requests are disabled (default)
    monkeypatch.setitem(app.config, "FILES_REST_ALLOW_RANGE_REQUESTS", False)

    extracted = file_service.extract_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    )

    # Simulate a request with Range header
    with app.test_request_context("/mock/path", headers={"Range": "bytes=0-9"}):
        response = extracted.send_file()

    # Should return 200 OK with full content, not 206
    assert response.status_code == 200
    assert response.headers.get("Accept-Ranges") is None
    # For direct_passthrough responses, consume the iterator to get data
    content = b"".join(response.iter_encoded())
    assert content == b"Hello world from a.txt.\n"


def test_container_item_range_requests_enabled(
    app, identity_simple, file_service, record_with_zip, monkeypatch
):
    """Test that Range requests work correctly when enabled.

    This tests the HTTP Range support for extracted container files.
    When FILES_REST_ALLOW_RANGE_REQUESTS is True, the response should:
    - Return 206 Partial Content for valid Range requests
    - Include Accept-Ranges and Content-Range headers
    - Return only the requested bytes
    """
    recid = record_with_zip["id"]

    # Enable Range requests
    monkeypatch.setitem(app.config, "FILES_REST_ALLOW_RANGE_REQUESTS", True)

    # Test 1: Valid Range request (bytes 0-9)
    extracted = file_service.extract_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    )
    with app.test_request_context("/mock/path", headers={"Range": "bytes=0-9"}):
        response = extracted.send_file()

    assert response.status_code == 206
    assert response.headers.get("Accept-Ranges") == "bytes"
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"].startswith("bytes 0-9/")
    # For direct_passthrough responses, consume the iterator to get data
    content = b"".join(response.iter_encoded())
    assert content == b"Hello worl"  # First 10 bytes (0-9)

    # Test 2: Range from offset to end (bytes 10-)
    extracted = file_service.extract_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    )
    with app.test_request_context("/mock/path", headers={"Range": "bytes=10-"}):
        response = extracted.send_file()

    assert response.status_code == 206
    assert response.headers.get("Accept-Ranges") == "bytes"
    # For direct_passthrough responses, consume the iterator to get data
    content = b"".join(response.iter_encoded())
    assert content == b"d from a.txt.\n"  # Bytes 10 to end

    # Test 3: Range beyond file size should return 416
    extracted = file_service.extract_container_item(
        identity_simple, recid, "testzip.zip", "a.txt"
    )
    with pytest.raises(RequestedRangeNotSatisfiable):
        with app.test_request_context("/mock/path", headers={"Range": "bytes=9999-"}):
            extracted.send_file()


def test_container_item_no_range_for_iterable_stream(
    app, identity_simple, file_service, record_with_zip, monkeypatch
):
    """Test that non-seekable iterable streams do not support Range requests.

    Streams that are iterable (like GeneratorReader for directory ZIPs) are not
    seekable and should never advertise Range support.
    """
    from invenio_records_resources.services.files.extractors.zip import GeneratorReader

    recid = record_with_zip["id"]

    # Enable Range requests
    monkeypatch.setitem(app.config, "FILES_REST_ALLOW_RANGE_REQUESTS", True)

    # Create a mock iterable stream (simulating a generated directory ZIP)
    def gen():
        yield b"test data"

    class MockStream(GeneratorReader):
        iterable = gen()

    mock_stream = MockStream(gen(), "test.txt")

    # Create ContainerItemResult with the iterable stream
    from invenio_records_resources.services.files.results import ContainerItemResult

    result = ContainerItemResult(
        None,
        None,
        None,
        None,
        mock_stream,
        "test.txt",
        size=None,
        mimetype="application/octet-stream",
    )

    # Even with Range requests enabled, iterable streams should not support Range
    with app.test_request_context("/mock/path", headers={"Range": "bytes=0-4"}):
        response = result.send_file()

    # Should return 200 OK, not 206
    assert response.status_code == 200
    assert response.headers.get("Accept-Ranges") is None


def test_large_zip_memory_usage(
    file_service, location, example_record, identity_simple
):
    """Test that extracting from and listing a ZIP file with suspicious compression ratio will raise an exception."""

    recid = example_record["id"]
    metadata = {"type": "zip"}
    file_service.init_files(
        identity_simple,
        recid,
        data=[
            {
                "key": "huge_test.zip",
                "metadata": metadata,
                "access": {"hidden": False},
            }
        ],
    )

    # Create a large zip in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("huge_test/", "")
        # Add a few large files
        for i in range(10):
            zipf.writestr(f"huge_test/largefile_{i}.bin", b"x" * 50_000_000)
    zip_buffer.seek(0)

    file_service.set_file_content(identity_simple, recid, "huge_test.zip", zip_buffer)
    file_service.commit_file(identity_simple, recid, "huge_test.zip")
    with pytest.raises(InvalidFileContentError):
        file_service.list_container(identity_simple, recid, "huge_test.zip")
    with pytest.raises(InvalidFileContentError):
        file_service.extract_container_item(
            identity_simple,
            recid,
            "huge_test.zip",
            "huge_test",  # entire zip
        )
