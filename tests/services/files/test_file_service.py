# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File service tests."""

from io import BytesIO
from unittest.mock import patch

import pytest
from invenio_access.permissions import system_identity
from invenio_files_rest.errors import FileSizeError
from marshmallow import ValidationError

from invenio_records_resources.services.errors import (
    FileKeyNotFoundError,
    PermissionDeniedError,
)

#
# Fixtures
#


@pytest.fixture(scope="module")
def mock_request():
    """Patch response raw."""

    # Mock HTTP request
    class MockResponse:
        """Mock response."""

        raw = BytesIO(b"test file content")

    class MockRequest:
        """Mock request."""

        def __enter__(self):
            """Mock ctx manager."""
            return MockResponse()

        def __exit__(self, *args):
            """Mock ctx manager."""
            pass

    return MockRequest()


#
# Local files
#


def test_file_flow(file_service, location, example_file_record, identity_simple, db):
    """Test the lifecycle of a file.

    - Initialize file saving
    - Save 1 files
    - Commit the files
    - List files of the record
    - Read file metadata
    - Retrieve a file
    - Delete a file
    - Delete all remaining files
    - List should be empty
    """
    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "checksum": "md5:c785060c866796cc2a1708c997154c8e",
            "size": 17,  # 2kB
            "metadata": {
                "description": "Published article PDF.",
            },
        }
    ]
    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]
    # for to_file in to_files:
    content = BytesIO(b"test file content")
    result = file_service.set_file_content(
        identity_simple,
        recid,
        file_to_initialise[0]["key"],
        content,
        content.getbuffer().nbytes,
    )
    # TODO figure response for succesfully saved file
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]

    result = file_service.commit_file(identity_simple, recid, "article.txt")
    # TODO currently there is no status in the json between the initialisation
    # and the commiting.
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]

    # List files
    result = file_service.list_files(identity_simple, recid)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]
    assert result.to_dict()["entries"][0]["storage_class"] == "L"
    assert "uri" not in result.to_dict()["entries"][0]

    # Read file metadata
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]
    assert result.to_dict()["storage_class"] == "L"

    # Retrieve file
    result = file_service.get_file_content(identity_simple, recid, "article.txt")
    assert result.file_id == "article.txt"

    # Delete file
    result = file_service.delete_file(identity_simple, recid, "article.txt")
    assert result.file_id == "article.txt"

    # Assert deleted
    result = file_service.list_files(identity_simple, recid)
    assert result.entries
    assert len(list(result.entries)) == 0

    # Delete all remaining files
    result = file_service.delete_all_files(identity_simple, recid)
    assert list(result.entries) == []


def test_init_files(file_service, location, example_file_record, identity_simple):
    """Test the initialization of local files, with different metadata and access."""
    recid = example_file_record["id"]

    # Pass an object with missing required field
    file_to_initialise = [{}]

    with pytest.raises(ValidationError) as e:
        file_service.init_files(identity_simple, recid, file_to_initialise)

    error = e.value
    assert {
        0: {"key": ["Missing data for required field."]}
    } == error.normalized_messages()

    # Pass an object with added field
    file_to_initialise = [
        {"key": "article.txt", "metadata": {"foo": "bar"}},
        {"key": "article.csv", "metadata": {"foo": "baz"}, "access": {"hidden": True}},
    ]

    result = file_service.init_files(identity_simple, recid, file_to_initialise)

    first_entry = result.to_dict()["entries"][0]
    assert file_to_initialise[0]["key"] == first_entry["key"]
    assert file_to_initialise[0]["metadata"] == first_entry["metadata"]
    assert first_entry["access"]["hidden"] is False  # default value

    second_entry = result.to_dict()["entries"][1]
    assert file_to_initialise[1]["key"] == second_entry["key"]
    assert file_to_initialise[1]["metadata"] == second_entry["metadata"]
    assert second_entry["access"]["hidden"] is True


#
# External files
#


@patch("invenio_records_resources.services.files.tasks.requests.get")
def test_external_file_simple_flow(
    p_response_raw,
    mock_request,
    file_service,
    example_file_record,
    identity_simple,
    location,
):
    """Test the lifecycle of an external file.

    - Initialize file saving
    - "Wait for completion by the task"
    - List files of the record
    - Read file metadata
    - Retrieve a file
    - Delete a file
    - Delete all remaining files
    - List should be empty
    """

    p_response_raw.return_value = mock_request

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "uri": "https://inveniordm.test/files/article.txt",
            "transfer_type": "F",
        }
    ]

    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]

    # WAIT FOR COMPLETION BY THE TASK

    # List files
    result = file_service.list_files(identity_simple, recid)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]

    # Read file metadata
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["storage_class"] == "L"  # changed after commit
    assert "uri" not in result

    # Retrieve file
    result = file_service.get_file_content(identity_simple, recid, "article.txt")
    assert result.file_id == "article.txt"
    with result.get_stream("rb") as stream:
        assert stream.read() == b"test file content"

    # Delete file
    result = file_service.delete_file(identity_simple, recid, "article.txt")
    assert result.file_id == "article.txt"

    # Assert deleted
    result = file_service.list_files(identity_simple, recid)
    assert result.entries
    assert len(list(result.entries)) == 0

    # Delete all remaining files
    result = file_service.delete_all_files(identity_simple, recid)
    assert list(result.entries) == []


def test_external_file_invalid_url(
    file_service, example_file_record, identity_simple, location
):
    """Test invalid URL as URI."""

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "uri": "invalid",
            "storage_class": "F",
        }
    ]

    with pytest.raises(ValidationError):
        file_service.init_files(identity_simple, recid, file_to_initialise)


@patch("invenio_records_resources.services.files.tasks.requests.get")
@patch("invenio_records_resources.services.files.transfer.providers.fetch.fetch_file")
def test_content_and_commit_external_file(
    p_fetch_file,
    p_response_raw,
    mock_request,
    file_service,
    example_file_record,
    identity_simple,
    location,
):
    """
    - Initialize file, should be fetch (is external). Task is mocked, so it won"t be fetched.
    - Set content as user (test a /content request) --> 403
    - Set content as system (test task set content) --> Success
    - Commit as user (test a /commit request) --> 403
    - Commit as system (test task commit) --> Success
    """
    p_response_raw.return_value = mock_request

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "uri": "https://inveniordm.test/files/article.txt",
            "transfer_type": "F",
        }
    ]

    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]

    # Check it is still external
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer_type"] == "F"

    # Set content as user
    content = BytesIO(b"test file content")
    with pytest.raises(PermissionDeniedError):
        file_service.set_file_content(
            identity_simple,
            recid,
            file_to_initialise[0]["key"],
            content,
            content.getbuffer().nbytes,
        )

    # Set content as system
    result = file_service.set_file_content(
        system_identity,
        recid,
        file_to_initialise[0]["key"],
        content,
        content.getbuffer().nbytes,
    )
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer_type"] == "F"  # not commited yet
    assert "uri" not in result

    # Commit as user
    with pytest.raises(PermissionDeniedError):
        file_service.commit_file(identity_simple, recid, "article.txt")

    # Commit as system
    result = file_service.commit_file(system_identity, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer_type"] == "L"
    assert "uri" not in result


@patch("invenio_records_resources.services.files.tasks.requests.get")
@patch("invenio_records_resources.services.files.transfer.providers.fetch.fetch_file")
def test_delete_not_committed_external_file(
    p_fetch_file,
    p_response_raw,
    mock_request,
    file_service,
    example_file_record,
    identity_simple,
    location,
):
    """
    - Initialize file, should be fetch (is external). Task is mocked, so it won"t be fetched.
    - Delete --> Success
    - Set content as system --> Fail (None)
    - Commit as system --> Fail (None)
    - Assert deleted
    """
    p_response_raw.return_value = mock_request

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "uri": "https://inveniordm.test/files/article.txt",
            "transfer_type": "F",
        }
    ]

    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]

    # Check it is still external
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer_type"] == "F"

    # Delete file
    file_service.delete_file(identity_simple, recid, "article.txt")
    with pytest.raises(FileKeyNotFoundError):
        result = file_service.read_file_metadata(identity_simple, recid, "article.txt")

    # Assert deleted
    result = file_service.list_files(identity_simple, recid)
    assert result.entries
    assert len(list(result.entries)) == 0

    # Set content as system
    content = BytesIO(b"test file content")
    with pytest.raises(FileKeyNotFoundError):
        result = file_service.set_file_content(
            system_identity,
            recid,
            file_to_initialise[0]["key"],
            content,
            content.getbuffer().nbytes,
        )

    with pytest.raises(FileKeyNotFoundError):
        result = file_service.read_file_metadata(identity_simple, recid, "article.txt")

    # Commit as system
    with pytest.raises(FileKeyNotFoundError):
        assert file_service.commit_file(system_identity, recid, "article.txt")

    # Assert deleted
    result = file_service.list_files(identity_simple, recid)
    assert result.entries
    assert len(list(result.entries)) == 0


@patch("invenio_records_resources.services.files.tasks.requests.get")
@patch("invenio_records_resources.services.files.transfer.providers.fetch.fetch_file")
def test_read_not_committed_external_file(
    p_fetch_file,
    p_response_raw,
    mock_request,
    file_service,
    example_file_record,
    identity_simple,
    location,
):
    """
    - Initialize file, should be fetch (is external). Task is mocked, so it won"t be fetched.
    - List and read file metadata --> Success
    - Retrieve file --> 403
    """
    p_response_raw.return_value = mock_request

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "uri": "https://inveniordm.test/files/article.txt",
            "transfer_type": "F",
        }
    ]
    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]

    # Check it is still external
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer_type"] == "F"

    # List files
    result = file_service.list_files(identity_simple, recid)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]

    # Read file metadata
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer_type"] == "F"  # changed after commit

    # Retrieve file
    with pytest.raises(PermissionDeniedError):
        file_service.get_file_content(identity_simple, recid, "article.txt")


@pytest.mark.parametrize("allow_empty_files", [True, False])
def test_empty_files(
    file_service,
    location,
    example_file_record,
    identity_simple,
    allow_empty_files,
    monkeypatch,
    base_app,
):
    """Test the lifecycle of an empty file."""
    monkeypatch.setitem(
        base_app.config, "RECORDS_RESOURCES_ALLOW_EMPTY_FILES", allow_empty_files
    )
    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "checksum": "md5:c785060c866796cc2a1708c997154c8e",
            "size": 0,  # 2kB
            "metadata": {
                "description": "Published article PDF.",
            },
        }
    ]
    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]
    # for to_file in to_files:
    content = BytesIO()
    result = file_service.set_file_content(
        identity_simple,
        recid,
        file_to_initialise[0]["key"],
        content,
        content.getbuffer().nbytes,
    )
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]

    if allow_empty_files:
        result = file_service.commit_file(identity_simple, recid, "article.txt")
        assert result.to_dict()["key"] == file_to_initialise[0]["key"]
    else:
        with pytest.raises(FileSizeError):
            result = file_service.commit_file(identity_simple, recid, "article.txt")


def test_multipart_file_upload_local_storage(
    file_service, location, example_file_record, identity_simple
):
    """Test the multipart upload to the local storage.

    - Initialize file saving
    - Save 1 files via multipart upload
    - Commit the files
    - List files of the record
    - Read file metadata
    - Retrieve a file
    """
    recid = example_file_record["id"]
    key = "article.txt"
    file_to_initialise = [
        {
            "key": key,
            "checksum": "md5:c785060c866796cc2a1708c997154c8e",
            "size": 17,  # 2kB
            "metadata": {
                "description": "Published article PDF.",
            },
            "transfer_type": "M",
            "parts": 2,
            "part_size": 10,
        }
    ]
    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    result = result.to_dict()

    assert result["entries"][0]["key"] == key
    assert "parts" in result["entries"][0]["links"]

    def upload_part(part_no, part_content, part_size):
        # for to_file in to_files:
        return file_service.set_multipart_file_content(
            identity_simple,
            recid,
            key,
            part_no,
            BytesIO(part_content),
            part_size,
        )

    content = b"test file content"
    result = upload_part(1, content[:10], 10)
    assert result.to_dict()["key"] == key

    result = upload_part(2, content[10:], 7)
    assert result.to_dict()["key"] == key

    result = file_service.commit_file(identity_simple, recid, "article.txt")
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]

    # List files
    result = file_service.list_files(identity_simple, recid)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]
    assert result.to_dict()["entries"][0]["storage_class"] == "L"
    assert "uri" not in result.to_dict()["entries"][0]

    # Read file metadata
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]
    assert result.to_dict()["transfer_type"] == "L"
    assert "uri" not in result.to_dict()

    # Retrieve file
    result = file_service.get_file_content(identity_simple, recid, "article.txt")
    assert result.file_id == "article.txt"
