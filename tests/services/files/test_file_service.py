# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File service tests."""

from io import BytesIO
from unittest.mock import patch

import pytest
from flask_principal import Identity
from invenio_access import any_user
from invenio_access.permissions import system_identity
from invenio_db.uow import UnitOfWork
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import FileInstance, ObjectVersion
from marshmallow import ValidationError

from invenio_records_resources.services.errors import (
    FileKeyNotFoundError,
    PermissionDeniedError,
    TransferException,
)
from tests.mock_module.models import FileRecordMetadata

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
        status_code = 200

    class MockRequest:
        """Mock request."""

        def __enter__(self):
            """Mock ctx manager."""
            return MockResponse()

        def __exit__(self, *args):
            """Mock ctx manager."""
            pass

    return MockRequest()


@pytest.fixture(scope="module")
def mock_404_request():
    """Patch response raw."""

    # Mock HTTP request
    class MockResponse:
        """Mock response."""

        raw = BytesIO(b"not found")
        status_code = 404
        text = "not found"

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
    file_result = result.to_dict()["entries"][0]
    assert file_result["key"] == file_to_initialise[0]["key"]
    assert file_result["checksum"] == file_to_initialise[0]["checksum"]
    assert file_result["size"] == file_to_initialise[0]["size"]
    assert file_result["metadata"] == file_to_initialise[0]["metadata"]
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


def test_retrieve_non_existing_file(
    file_service, location, example_file_record, identity_simple, db
):
    """Test if accessing a non-existing file raises a correct error."""
    recid = example_file_record["id"]

    # Retrieve file
    with pytest.raises(FileKeyNotFoundError):
        file_service.get_file_content(identity_simple, recid, "does_not_exist.txt")


#
# External fetched files
#


@patch("invenio_records_resources.services.files.tasks.requests.get")
def test_fetch_file_simple_flow(
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
            "transfer": {
                "url": "https://inveniordm.test/files/article.txt",
                "type": "F",
            },
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
    assert result["transfer"]["type"] == "L"  # changed after commit
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


def test_fetch_file_invalid_url(
    file_service, example_file_record, identity_simple, location
):
    """Test invalid URL as URI."""

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "transfer": {
                "url": "invalid",
                "type": "F",
            },
        }
    ]

    with pytest.raises(ValidationError):
        file_service.init_files(identity_simple, recid, file_to_initialise)


@patch("invenio_records_resources.services.files.tasks.requests.get")
def test_fetch_unreadable_file(
    p_response_raw,
    mock_404_request,
    file_service,
    example_file_record,
    identity_simple,
    location,
):
    """Test fetching non-existing file."""

    p_response_raw.return_value = mock_404_request

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "transfer": {
                "url": "https://inveniordm.test/files/article-that-does-not-exist.txt",
                "type": "F",
            },
        }
    ]

    file_service.init_files(identity_simple, recid, file_to_initialise)

    # List files
    result = file_service.list_files(identity_simple, recid)
    assert result.to_dict()["entries"][0]["status"] == "failed"
    assert result.to_dict()["entries"][0]["transfer"]["error"] == "not found"


@patch("invenio_records_resources.services.files.tasks.requests.get")
@patch("invenio_records_resources.services.files.transfer.providers.fetch.fetch_file")
def test_content_and_commit_fetched_file(
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
            "transfer": {
                "type": "F",
                "url": "https://inveniordm.test/files/article.txt",
            },
        }
    ]

    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]

    # Check it is still external
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer"]["type"] == "F"

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
    assert result["transfer"]["type"] == "F"  # not commited yet
    assert "uri" not in result

    # Commit as user
    with pytest.raises(PermissionDeniedError):
        file_service.commit_file(identity_simple, recid, "article.txt")

    # Commit as system
    result = file_service.commit_file(system_identity, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer"]["type"] == "L"
    assert "uri" not in result


@patch("invenio_records_resources.services.files.tasks.requests.get")
@patch("invenio_records_resources.services.files.transfer.providers.fetch.fetch_file")
def test_delete_not_committed_fetched_file(
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
            "transfer": {
                "type": "F",
                "url": "https://inveniordm.test/files/article.txt",
            },
        }
    ]

    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]

    # Check it is still external
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer"]["type"] == "F"

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
def test_read_not_committed_fetched_file(
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
            "transfer": {
                "type": "F",
                "url": "https://inveniordm.test/files/article.txt",
            },
        }
    ]
    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]

    # Check it is still external
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer"]["type"] == "F"

    # List files
    result = file_service.list_files(identity_simple, recid)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]

    # Read file metadata
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    result = result.to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer"]["type"] == "F"  # changed after commit

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
            "transfer": {
                "type": "M",
                "parts": 2,
                "part_size": 10,
            },
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

    # Read file metadata
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]
    assert result.to_dict()["transfer"]["type"] == "L"

    # Retrieve file
    result = file_service.get_file_content(identity_simple, recid, "article.txt")
    assert result.file_id == "article.txt"


#
# External remote files
#


def test_remote_file(
    file_service,
    example_file_record,
    identity_simple,
    location,
):
    """Test the lifecycle of an external remote file."""

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "transfer": {
                "url": "https://inveniordm.test/files/article.txt",
                "type": "R",
            },
        }
    ]

    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    file_result = result.to_dict()["entries"][0]
    assert file_result["key"] == file_to_initialise[0]["key"]

    assert file_result["transfer"]["type"] == "R"
    assert "url" not in file_result["transfer"]
    assert file_result["status"] == "completed"

    sent_file = file_service.get_file_content(
        identity_simple, recid, "article.txt"
    ).send_file()
    assert sent_file.status_code == 302
    assert sent_file.headers["Location"] == "https://inveniordm.test/files/article.txt"


def test_remote_file_with_checksum_and_size(
    file_service,
    example_file_record,
    identity_simple,
    location,
):
    """Test the lifecycle of an external remote file."""

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "checksum": "md5:c785060c866796cc2a1708c997154c8e",
            "size": 17,
            "transfer": {
                "url": "https://inveniordm.test/files/article.txt",
                "type": "R",
            },
        }
    ]

    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    file_result = result.to_dict()["entries"][0]
    assert file_result["key"] == file_to_initialise[0]["key"]

    assert file_result["transfer"]["type"] == "R"
    assert "url" not in file_result["transfer"]
    assert file_result["status"] == "completed"

    assert file_result["checksum"] == "md5:c785060c866796cc2a1708c997154c8e"
    assert file_result["size"] == 17

    sent_file = file_service.get_file_content(
        identity_simple, recid, "article.txt"
    ).send_file()
    assert sent_file.status_code == 302
    assert sent_file.headers["Location"] == "https://inveniordm.test/files/article.txt"


def test_remote_file_no_permissions(
    file_service,
    example_file_record,
    location,
):
    """Test the lifecycle of an external remote file."""

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "transfer": {
                "url": "https://inveniordm.test/files/article.txt",
                "type": "R",
            },
        }
    ]

    i = Identity(None)
    i.provides.add(any_user)

    with pytest.raises(PermissionDeniedError):
        file_service.init_files(i, recid, file_to_initialise)


def test_backward_compatibility(
    file_service, location, example_file_record, identity_simple, db
):
    """Test the backward compatibility to make sure that files without a transfer section still work.

    - Initialize file saving
    - Save 1 file
    - Commit the file
    - Directly in the database, remove the transfer section
    - List files of the record
    - Retrieve a file
    - Delete a file
    """

    # same code as in the test_file_flow, so skipping the checks to make the test shorter
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
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    content = BytesIO(b"test file content")
    result = file_service.set_file_content(
        identity_simple,
        recid,
        file_to_initialise[0]["key"],
        content,
        content.getbuffer().nbytes,
    )
    result = file_service.commit_file(identity_simple, recid, "article.txt")

    # remove the transfer section from the database and make sure it is not there
    file_metadata = FileRecordMetadata.query.all()
    assert len(file_metadata) == 1
    file_metadata[0].json = {
        k: v for k, v in file_metadata[0].json.items() if k != "transfer"
    }
    db.session.add(file_metadata[0])
    db.session.commit()
    db.session.refresh(file_metadata[0])
    assert "transfer" not in file_metadata[0].json

    # List files
    result = file_service.list_files(identity_simple, recid)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]
    assert result.to_dict()["entries"][0]["storage_class"] == "L"
    assert result.to_dict()["entries"][0]["transfer"] == {"type": "L"}
    assert "uri" not in result.to_dict()["entries"][0]

    # Read file metadata
    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]
    assert result.to_dict()["storage_class"] == "L"
    assert result.to_dict()["transfer"] == {"type": "L"}

    # Retrieve file
    result = file_service.get_file_content(identity_simple, recid, "article.txt")
    assert result.file_id == "article.txt"
    assert result.get_stream("rb").read() == b"test file content"

    # Delete file
    result = file_service.delete_file(identity_simple, recid, "article.txt")
    assert result.file_id == "article.txt"

    # Assert deleted
    result = file_service.list_files(identity_simple, recid)
    assert result.entries
    assert len(list(result.entries)) == 0


def test_staged_file_flow(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """End-to-end staged-local upload (init -> content -> commit)."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})

    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "checksum": "md5:c785060c866796cc2a1708c997154c8e",
            "size": 17,
            "metadata": {"description": "Published article PDF."},
        }
    ]

    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    entry = result.to_dict()["entries"][0]
    assert entry["key"] == "article.txt"
    assert entry["transfer"]["type"] == "SL"
    assert entry["status"] == "pending"

    content = BytesIO(b"test file content")
    result = file_service.set_file_content(
        identity_simple,
        recid,
        "article.txt",
        content,
        content.getbuffer().nbytes,
    )
    assert result.to_dict()["key"] == "article.txt"
    assert result.to_dict()["status"] == "completed"

    result = file_service.commit_file(identity_simple, recid, "article.txt")
    assert result.to_dict()["key"] == "article.txt"

    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert db_record.files["article.txt"].transfer.transfer_type == "SL"
    fi = db_record.files["article.txt"].object_version.file
    assert fi.readable is True
    assert fi.size == 17
    assert db_record.bucket.size == 17

    result = file_service.read_file_metadata(identity_simple, recid, "article.txt")
    assert result.to_dict()["key"] == "article.txt"
    assert result.to_dict()["storage_class"] == "L"
    assert result.to_dict()["size"] == 17

    result = file_service.get_file_content(identity_simple, recid, "article.txt")
    with result.get_stream("rb") as stream:
        assert stream.read() == b"test file content"


def test_staged_flag_off_keeps_local(
    file_service, location, example_file_record, identity_simple, db
):
    """With the flag off, ``L`` stays ``L``."""
    recid = example_file_record["id"]
    file_to_initialise = [
        {
            "key": "article.txt",
            "checksum": "md5:c785060c866796cc2a1708c997154c8e",
            "size": 17,
        }
    ]

    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    assert result.to_dict()["entries"][0]["transfer"]["type"] == "L"

    content = BytesIO(b"test file content")
    file_service.set_file_content(
        identity_simple,
        recid,
        "article.txt",
        content,
        content.getbuffer().nbytes,
    )
    file_service.commit_file(identity_simple, recid, "article.txt")

    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert db_record.files["article.txt"].transfer.transfer_type == "L"


def test_staged_set_file_content_rejects_external_uow(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """Passing an external uow with a staged transfer raises TransferException."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})

    recid = example_file_record["id"]
    file_service.init_files(
        identity_simple,
        recid,
        [{"key": "article.txt", "size": 17}],
    )

    content = BytesIO(b"test file content")
    with UnitOfWork(db.session) as group_uow:
        with pytest.raises(TransferException, match="external unit of work"):
            file_service.set_file_content(
                identity_simple,
                recid,
                "article.txt",
                content,
                content.getbuffer().nbytes,
                uow=group_uow,
            )

    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    fr = db_record.files["article.txt"]
    assert fr.transfer.transfer_type == "SL"
    assert fr.object_version is not None
    assert fr.object_version.file is not None
    assert fr.object_version.file.readable is False


def test_pending_staged_file_skipped_by_dumper_and_manager(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """Pending staged files are skipped by the partial dumper and FilesManager properties.

    Staged init pre-allocates the OV/FI before bytes land. Code paths that
    check ``file_record.file is not None`` would otherwise observe a not-yet-
    readable FileInstance and either crash or emit misleading data.
    """
    from invenio_records_resources.records.dumpers import PartialFileDumper

    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})

    recid = example_file_record["id"]
    file_service.init_files(
        identity_simple,
        recid,
        [{"key": "done.txt"}, {"key": "pending.txt"}],
    )

    content = BytesIO(b"finalised-bytes")
    file_service.set_file_content(
        identity_simple, recid, "done.txt", content, content.getbuffer().nbytes
    )
    file_service.commit_file(identity_simple, recid, "done.txt")

    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    finalised = db_record.files["done.txt"]
    pending = db_record.files["pending.txt"]
    assert finalised.object_version.file.readable is True
    assert pending.object_version.file.readable is False

    # FilesManager properties only count finalised entries.
    assert db_record.files.total_bytes == len(b"finalised-bytes")
    mimetypes = db_record.files.mimetypes
    assert None not in mimetypes
    assert len(mimetypes) == 1

    # PartialFileDumper omits file fields for pending entries.
    dumped_done = PartialFileDumper().dump(finalised, {})
    dumped_pending = PartialFileDumper().dump(pending, {})
    assert "file_id" in dumped_done
    assert "file_id" not in dumped_pending


class _RaisingStream:
    """File-like that yields one chunk then raises ``OSError``."""

    def __init__(self, first_chunk):
        self._first_chunk = first_chunk
        self._yielded = False

    def read(self, n=-1):
        if not self._yielded:
            self._yielded = True
            return self._first_chunk
        raise OSError("simulated mid-stream failure")


def test_staged_failure_cleanup_and_retry(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """Mid-stream failure clears the pre-allocated rows so a retry works."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})

    recid = example_file_record["id"]
    file_service.init_files(identity_simple, recid, [{"key": "retry.bin"}])

    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    fr = db_record.files["retry.bin"]
    fr_id = fr.id
    ov_id = fr.object_version.version_id
    fi_id = fr.object_version.file_id

    result = file_service.set_file_content(
        identity_simple,
        recid,
        "retry.bin",
        _RaisingStream(b"some-bytes"),
        16,
    )
    assert result.errors

    # All three pre-allocated rows are gone.
    assert FileRecordMetadata.query.filter_by(id=fr_id).first() is None
    assert ObjectVersion.query.filter_by(version_id=ov_id).first() is None
    assert FileInstance.query.filter_by(id=fi_id).first() is None
    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert "retry.bin" not in db_record.files

    # Retrying the same key works end-to-end.
    file_service.init_files(identity_simple, recid, [{"key": "retry.bin"}])
    content = BytesIO(b"happy path bytes")
    file_service.set_file_content(
        identity_simple,
        recid,
        "retry.bin",
        content,
        content.getbuffer().nbytes,
    )
    file_service.commit_file(identity_simple, recid, "retry.bin")

    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    fi = db_record.files["retry.bin"].object_version.file
    assert fi.readable is True
    assert fi.size == len(b"happy path bytes")


@patch("invenio_records_resources.services.files.tasks.requests.get")
def test_staged_fetch_simple_flow(
    p_response_raw,
    file_service,
    example_file_record,
    identity_simple,
    location,
    set_app_config_fn_scoped,
):
    """With the flag on, ``F`` is rewritten to ``SF`` and ends as ``SL``."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})

    # Inline mock — the module-scoped ``mock_request`` fixture has a
    # single ``BytesIO`` that's drained by whichever fetch test runs
    # first.
    class _Response:
        raw = BytesIO(b"test file content")
        status_code = 200

    class _Request:
        def __enter__(self):
            return _Response()

        def __exit__(self, *args):
            pass

    p_response_raw.return_value = _Request()

    recid = example_file_record["id"]
    result = file_service.init_files(
        identity_simple,
        recid,
        [
            {
                "key": "article.txt",
                "transfer": {
                    "url": "https://inveniordm.test/files/article.txt",
                    "type": "F",
                },
            }
        ],
    )
    # The fetch celery task runs eagerly during the init UoW commit, so
    # by the time we get here the file is already fetched and finalized.
    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    fr = db_record.files["article.txt"]
    assert fr.transfer.transfer_type == "SL"
    fi = fr.object_version.file
    assert fi.readable is True
    assert fi.size == len(b"test file content")

    # Bytes are reachable through the regular content endpoint.
    content = file_service.get_file_content(identity_simple, recid, "article.txt")
    with content.get_stream("rb") as stream:
        assert stream.read() == b"test file content"


@patch("invenio_records_resources.services.files.tasks.requests.get")
def test_staged_fetch_flag_off_keeps_fetch(
    p_response_raw,
    file_service,
    example_file_record,
    identity_simple,
    location,
):
    """With the flag off, ``F`` stays the legacy fetch flow ending in ``L``."""

    class _Response:
        raw = BytesIO(b"test file content")
        status_code = 200

    class _Request:
        def __enter__(self):
            return _Response()

        def __exit__(self, *args):
            pass

    p_response_raw.return_value = _Request()

    recid = example_file_record["id"]
    file_service.init_files(
        identity_simple,
        recid,
        [
            {
                "key": "article.txt",
                "transfer": {
                    "url": "https://inveniordm.test/files/article.txt",
                    "type": "F",
                },
            }
        ],
    )

    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert db_record.files["article.txt"].transfer.transfer_type == "L"


def test_staged_sl_completes_after_flag_flip(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """An SL upload init'd with the flag on completes after the flag is off."""
    recid = example_file_record["id"]

    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    file_service.init_files(identity_simple, recid, [{"key": "rolled.txt"}])
    assert (
        file_service.record_cls.pid.resolve(recid, registered_only=False)
        .files["rolled.txt"]
        .transfer.transfer_type
        == "SL"
    )

    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": False})

    content = BytesIO(b"after-flip-bytes")
    file_service.set_file_content(
        identity_simple, recid, "rolled.txt", content, content.getbuffer().nbytes
    )
    file_service.commit_file(identity_simple, recid, "rolled.txt")

    fr = file_service.record_cls.pid.resolve(recid, registered_only=False).files[
        "rolled.txt"
    ]
    assert fr.transfer.transfer_type == "SL"
    assert fr.object_version.file.readable is True
    assert fr.object_version.file.size == len(b"after-flip-bytes")

    # New init with the flag off produces ``L``.
    file_service.init_files(identity_simple, recid, [{"key": "fresh.txt"}])
    fresh = file_service.record_cls.pid.resolve(recid, registered_only=False).files[
        "fresh.txt"
    ]
    assert fresh.transfer.transfer_type == "L"


@patch("invenio_records_resources.services.files.tasks.requests.get")
def test_staged_sf_completes_after_flag_flip(
    p_response_raw,
    file_service,
    example_file_record,
    identity_simple,
    location,
    set_app_config_fn_scoped,
):
    """An SF upload init'd with the flag on completes after the flag is off."""

    class _Response:
        raw = BytesIO(b"after-flip-bytes")
        status_code = 200

    class _Request:
        def __enter__(self):
            return _Response()

        def __exit__(self, *args):
            pass

    p_response_raw.return_value = _Request()

    recid = example_file_record["id"]

    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    file_service.init_files(
        identity_simple,
        recid,
        [
            {
                "key": "rolled.txt",
                "transfer": {
                    "url": "https://inveniordm.test/files/rolled.txt",
                    "type": "F",
                },
            }
        ],
    )

    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": False})

    fr = file_service.record_cls.pid.resolve(recid, registered_only=False).files[
        "rolled.txt"
    ]
    # Fetch ran eagerly during init_files; commit flipped SF -> SL.
    assert fr.transfer.transfer_type == "SL"
    assert fr.object_version.file.readable is True
    assert fr.object_version.file.size == len(b"after-flip-bytes")

    class _Response2:
        raw = BytesIO(b"fresh-bytes")
        status_code = 200

    class _Request2:
        def __enter__(self):
            return _Response2()

        def __exit__(self, *args):
            pass

    p_response_raw.return_value = _Request2()

    file_service.init_files(
        identity_simple,
        recid,
        [
            {
                "key": "fresh.txt",
                "transfer": {
                    "url": "https://inveniordm.test/files/fresh.txt",
                    "type": "F",
                },
            }
        ],
    )

    fresh = file_service.record_cls.pid.resolve(recid, registered_only=False).files[
        "fresh.txt"
    ]
    # Legacy fetch ran and flipped F -> L.
    assert fresh.transfer.transfer_type == "L"
