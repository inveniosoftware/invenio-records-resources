from os.path import dirname, join
from unittest.mock import MagicMock

import pytest

from invenio_records_resources.services.files.components import processor
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
    assert extracted_data.get_data() == b"Hello world from a.txt.\n"
