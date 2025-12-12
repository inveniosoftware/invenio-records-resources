# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 European Union.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resource tests for zip files."""

from unittest.mock import MagicMock

import pytest

from invenio_records_resources.services.files.components import processor
from invenio_records_resources.services.files.transfer import TransferStatus
from invenio_records_resources.tasks import extract_file_metadata


@pytest.fixture()
def record_before_file_init(
    file_service, location, example_record, identity_simple, zip_fp, monkeypatch
):
    """Image metadata extraction."""
    # Patch celery task
    task = MagicMock()
    monkeypatch.setattr(processor, "extract_file_metadata", task)

    return example_record


@pytest.fixture()
def record_with_zip_before_commit(
    file_service,
    location,
    record_before_file_init,
    identity_simple,
    zip_fp,
    monkeypatch,
):
    """Image metadata extraction."""
    recid = record_before_file_init["id"]

    # Upload file
    file_service.init_files(identity_simple, recid, [{"key": "testzip.zip"}])
    file_service.set_file_content(identity_simple, recid, "testzip.zip", zip_fp)

    return record_before_file_init


@pytest.fixture()
def record_with_zip(
    file_service,
    location,
    record_with_zip_before_commit,
    identity_simple,
    zip_fp,
    monkeypatch,
):
    """Image metadata extraction."""
    # Patch celery task
    task = MagicMock()
    monkeypatch.setattr(processor, "extract_file_metadata", task)

    recid = record_with_zip_before_commit["id"]

    # Commit (should send celery task)
    assert not task.apply_async.called
    file_service.commit_file(identity_simple, recid, "testzip.zip")
    assert task.apply_async.called

    # Call task manually
    extract_file_metadata(*task.apply_async.call_args[1]["args"])

    return record_with_zip_before_commit


@pytest.fixture()
def text_fp(tmp_path):
    """A test text file."""
    test_file = tmp_path / "testfile.txt"
    test_file.write_text("This is a dummy test file.\nLine 2: sample content.")
    with open(test_file, "rb") as fp:
        yield fp


def test_extractors_listing_extract_resource(
    file_service, location, record_with_zip, identity_simple, text_fp, client, headers
):
    """Test extraction API with a dummy extractor."""
    recid = record_with_zip["id"]

    # Get the file metadata
    res = client.get(f"/mocks/{recid}/files/testzip.zip")
    assert res.json["metadata"]["zip_toc_position"] == 236

    res = client.get(
        f"/mocks/{recid}/files/testzip.zip/container",
        headers=headers,
    )
    assert res.status_code == 200
    listing = res.json
    print(listing)
    assert listing == {
        "entries": [
            {
                "compressed_size": 24,
                "crc": 3057564182,
                "key": "a.txt",
                "links": {
                    "content": f"https://127.0.0.1:5000/api/mocks/{recid}/files/testzip.zip/container/a.txt"
                },
                "mimetype": "text/plain",
                "size": 24,
            },
            {
                "compressed_size": 24,
                "crc": 3057564182,
                "key": "b.txt",
                "links": {
                    "content": f"https://127.0.0.1:5000/api/mocks/{recid}/files/testzip.zip/container/b.txt"
                },
                "mimetype": "text/plain",
                "size": 24,
            },
            {
                "compressed_size": 24,
                "crc": 3057564182,
                "key": "c.txt",
                "links": {
                    "content": f"https://127.0.0.1:5000/api/mocks/{recid}/files/testzip.zip/container/c.txt"
                },
                "mimetype": "text/plain",
                "size": 24,
            },
            {
                "compressed_size": 24,
                "crc": 3057564182,
                "key": "d.txt",
                "links": {
                    "content": f"https://127.0.0.1:5000/api/mocks/{recid}/files/testzip.zip/container/d.txt"
                },
                "mimetype": "text/plain",
                "size": 24,
            },
        ],
        "folders": [],
        "total": 4,
        "truncated": False,
    }

    res = client.get(
        f"/mocks/{recid}/files/testzip.zip/container/a.txt",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.data == b"Hello world from a.txt.\n"


def test_zip_metadata_without_files_init(
    file_service, location, example_record, identity_simple, text_fp, client, headers
):
    recid = example_record["id"]
    # Make a GET request for a record with uninitialized files and check that status code is 404
    res = client.get(f"/mocks/{recid}/files/testzip.zip", headers=headers)
    assert res.status_code == 404


def test_zip_metadata_without_files_commit(
    file_service,
    location,
    record_with_zip_before_commit,
    identity_simple,
    text_fp,
    client,
    headers,
):
    recid = record_with_zip_before_commit["id"]
    # Make a GET request for an uncommited file and check that status is pending and zip_toc_position is not in the metadata
    res = client.get(f"/mocks/{recid}/files/testzip.zip", headers=headers)
    assert res.status_code == 200
    assert res.json["status"] == TransferStatus.PENDING
    assert res.json["metadata"] is None


def test_zip_metadata_on_record_with_zip(
    file_service,
    location,
    record_with_zip,
    identity_simple,
    text_fp,
    client,
    headers,
):
    recid = record_with_zip["id"]
    # Make a GET request for a commited file and check that zip_toc_position is in the metadata
    res = client.get(f"/mocks/{recid}/files/testzip.zip", headers=headers)
    assert res.json["metadata"]["zip_toc_position"] == 236
