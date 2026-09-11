# SPDX-FileCopyrightText: 2020-2024 CERN.
# SPDX-FileCopyrightText: 2025 CESNET.
# SPDX-License-Identifier: MIT

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
from sqlalchemy.exc import OperationalError

from invenio_records_resources.services.errors import (
    FileKeyNotFoundError,
    PermissionDeniedError,
)
from invenio_records_resources.services.files.components import (
    FileContentComponent,
    FileServiceComponent,
)
from invenio_records_resources.services.files.tasks import cleanup_failed_upload
from invenio_records_resources.services.files.upload import (
    FileUpload,
    UploadConflict,
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
    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    file_metadata = FileRecordMetadata.query.filter_by(record_id=record.id).all()
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
    """Upload and commit a local file."""
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
    assert entry["transfer"]["type"] == "L"
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
    assert db_record.files["article.txt"].transfer.transfer_type == "L"
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
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """Enabling the option after initialization does not change the upload path."""
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
    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert db_record.files["article.txt"].object_version is None

    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})

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


def test_preallocated_file_content_accepts_external_uow(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """Use one transaction when the caller supplies it."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})

    recid = example_file_record["id"]
    file_service.init_files(
        identity_simple,
        recid,
        [{"key": "article.txt", "size": 17}],
    )

    content = BytesIO(b"test file content")
    with UnitOfWork(db.session) as group_uow:
        result = file_service.set_file_content(
            identity_simple,
            recid,
            "article.txt",
            content,
            content.getbuffer().nbytes,
            uow=group_uow,
        )
        assert result.errors is None
        group_uow.commit()

    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    fr = db_record.files["article.txt"]
    assert fr.transfer.transfer_type == "L"
    assert fr.object_version is not None
    assert fr.object_version.file is not None
    assert fr.object_version.file.readable is True
    assert fr.object_version.file.size == 17


def test_pending_staged_file_skipped_by_dumper_and_manager(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """Exclude pending files from dumps and file totals."""
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

    assert db_record.files.total_bytes == len(b"finalised-bytes")
    mimetypes = db_record.files.mimetypes
    assert None not in mimetypes
    assert len(mimetypes) == 1

    dumped_done = PartialFileDumper().dump(finalised, {})
    dumped_pending = PartialFileDumper().dump(pending, {})
    assert "file_id" in dumped_done
    assert "file_id" not in dumped_pending


class _RaisingStream:
    """Raise after returning one chunk."""

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
    """Clean up a failed upload so it can be retried."""
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

    assert FileRecordMetadata.query.filter_by(id=fr_id).first() is None
    assert ObjectVersion.query.filter_by(version_id=ov_id).first() is None
    assert FileInstance.query.filter_by(id=fi_id).first() is None
    db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert "retry.bin" not in db_record.files

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


@patch("invenio_records_resources.services.files.transfer.providers.fetch.fetch_file")
def test_preallocated_fetch_failure_preserves_record_and_error(
    p_fetch_file,
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """A failed fetch remains an ``F`` record and reports failed status."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    recid = example_file_record["id"]
    file_service.init_files(
        identity_simple,
        recid,
        [
            {
                "key": "failed-fetch.bin",
                "transfer": {
                    "type": "F",
                    "url": "https://inveniordm.test/files/failed-fetch.bin",
                },
            }
        ],
    )

    result = file_service.set_file_content(
        system_identity,
        recid,
        "failed-fetch.bin",
        _RaisingStream(b"partial"),
        16,
    )

    assert result.errors
    result = file_service.read_file_metadata(
        identity_simple, recid, "failed-fetch.bin"
    ).to_dict()
    assert result["transfer"]["type"] == "F"
    assert result["transfer"]["error"]
    assert result["status"] == "failed"


def test_pending_upload_deletion_cleans_attempt_and_allows_reinitialization(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """Deleting an active upload allows the key to be initialized again."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    recid = example_file_record["id"]
    file_service.init_files(identity_simple, recid, [{"key": "abandoned.bin"}])

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    claim = FileUpload(file_service)._prepare(record, "abandoned.bin", content_length=4)
    assert db.session.get(FileInstance, claim.file_instance_id).uri is not None

    file_service.delete_file(identity_simple, recid, "abandoned.bin")

    assert db.session.get(FileInstance, claim.file_instance_id) is None
    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert "abandoned.bin" not in record.files

    file_service.init_files(identity_simple, recid, [{"key": "abandoned.bin"}])
    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert "abandoned.bin" in record.files


def test_deleted_upload_cannot_finalize(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """A deleted upload cannot be finished."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    recid = example_file_record["id"]
    file_service.init_files(identity_simple, recid, [{"key": "deleted.bin"}])

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    upload = FileUpload(file_service)
    claim = upload._prepare(record, "deleted.bin", content_length=4)
    _uri, size, checksum = claim.storage.save(BytesIO(b"late"), size=4)

    file_service.delete_file(identity_simple, recid, "deleted.bin")

    with pytest.raises(UploadConflict, match="was deleted while it was being uploaded"):
        upload._finalize(claim, size, checksum)
    assert db.session.get(FileInstance, claim.file_instance_id) is None
    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert record.bucket.size == 0


def test_delete_all_files_cleans_pending_upload_attempts(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """Bulk deletion cleans pending uploads."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    recid = example_file_record["id"]
    file_service.init_files(
        identity_simple,
        recid,
        [{"key": "claimed.bin"}, {"key": "unclaimed.bin"}],
    )

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    claimed = FileUpload(file_service)._prepare(record, "claimed.bin", content_length=4)
    unclaimed_id = record.files["unclaimed.bin"].object_version.file_id

    result = file_service.delete_all_files(identity_simple, recid)

    assert [entry["key"] for entry in result.entries] == [
        "claimed.bin",
        "unclaimed.bin",
    ]
    assert db.session.get(FileInstance, claimed.file_instance_id) is None
    assert db.session.get(FileInstance, unclaimed_id) is None
    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert list(record.files) == []


def test_finishing_an_upload_twice_is_safe(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """Finishing twice does not count the same bytes twice."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    recid = example_file_record["id"]
    file_service.init_files(identity_simple, recid, [{"key": "once.bin"}])

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    upload = FileUpload(file_service)
    claim = upload._prepare(record, "once.bin", content_length=4)
    _uri, size, checksum = claim.storage.save(BytesIO(b"once"), size=4)

    upload._finalize(claim, size, checksum)
    upload._finalize(claim, size, checksum)

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert record.files["once.bin"].object_version.file.readable is True
    assert record.bucket.size == 4


def test_staged_upload_runs_components_around_content(
    file_service,
    location,
    example_file_record,
    identity_simple,
    monkeypatch,
    set_app_config_fn_scoped,
):
    """Run component hooks on either side of the staged content operation."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    events = []

    class BeforeContent(FileServiceComponent):
        def set_file_content(
            self, identity, id_, file_key, stream, content_length, record
        ):
            assert self.uow
            assert record.files[file_key].object_version.file.uri is None
            events.append("before")

    class AfterContent(FileServiceComponent):
        def set_file_content(
            self, identity, id_, file_key, stream, content_length, record
        ):
            assert self.uow
            assert record.files[file_key].is_readable
            events.append("after")

    components = list(file_service.config.components)
    content_index = components.index(FileContentComponent)
    components[content_index:content_index] = [BeforeContent]
    components.insert(content_index + 2, AfterContent)
    monkeypatch.setattr(file_service.config, "components", components)
    recid = example_file_record["id"]
    file_service.init_files(identity_simple, recid, [{"key": "components.bin"}])

    result = file_service.set_file_content(
        identity_simple, recid, "components.bin", BytesIO(b"data"), 4
    )

    assert result.errors is None
    assert events == ["before", "after"]


@pytest.mark.parametrize(
    ("failing_commit", "committed_before_error"),
    [(1, True), (2, True), (2, False)],
)
def test_upload_reconciles_uncertain_commits(
    file_service,
    location,
    example_file_record,
    identity_simple,
    set_app_config_fn_scoped,
    monkeypatch,
    failing_commit,
    committed_before_error,
):
    """Recover when a commit fails or its result is unknown."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    recid = example_file_record["id"]
    file_service.init_files(identity_simple, recid, [{"key": "uncertain.bin"}])

    original_commit = UnitOfWork.commit
    commit_count = 0

    def uncertain_commit(uow):
        nonlocal commit_count
        commit_count += 1
        if commit_count == failing_commit:
            if committed_before_error:
                original_commit(uow)
            # What SQLAlchemy raises when the connection dies at commit time.
            error = OperationalError(
                "COMMIT", {}, Exception("server closed the connection unexpectedly")
            )
            error.connection_invalidated = True
            raise error
        return original_commit(uow)

    monkeypatch.setattr(UnitOfWork, "commit", uncertain_commit)

    result = file_service.set_file_content(
        identity_simple,
        recid,
        "uncertain.bin",
        BytesIO(b"once"),
        4,
    )

    assert result.errors is None
    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert record.files["uncertain.bin"].is_readable
    assert record.bucket.size == 4


@patch("invenio_records_resources.services.files.tasks.requests.get")
def test_staged_fetch_simple_flow(
    p_response_raw,
    file_service,
    example_file_record,
    identity_simple,
    location,
    set_app_config_fn_scoped,
):
    """A fetched file remains ``F`` until it is committed as ``L``."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})

    # Use a fresh stream because the module fixture may already be consumed.
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
    fr = db_record.files["article.txt"]
    assert fr.transfer.transfer_type == "L"
    fi = fr.object_version.file
    assert fi.readable is True
    assert fi.size == len(b"test file content")

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
    """Use the existing fetch flow when the option is disabled."""

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


def test_preallocated_local_completes_after_flag_flip(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """Complete an initialized upload after disabling the option."""
    recid = example_file_record["id"]

    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    file_service.init_files(identity_simple, recid, [{"key": "rolled.txt"}])
    assert (
        file_service.record_cls.pid.resolve(recid, registered_only=False)
        .files["rolled.txt"]
        .transfer.transfer_type
        == "L"
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
    assert fr.transfer.transfer_type == "L"
    assert fr.object_version.file.readable is True
    assert fr.object_version.file.size == len(b"after-flip-bytes")

    file_service.init_files(identity_simple, recid, [{"key": "fresh.txt"}])
    fresh = file_service.record_cls.pid.resolve(recid, registered_only=False).files[
        "fresh.txt"
    ]
    assert fresh.transfer.transfer_type == "L"


@patch("invenio_records_resources.services.files.tasks.requests.get")
def test_preallocated_fetch_completes_after_flag_flip(
    p_response_raw,
    file_service,
    example_file_record,
    identity_simple,
    location,
    set_app_config_fn_scoped,
):
    """Keep the selected upload path after disabling the option."""

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
    assert fr.transfer.transfer_type == "L"
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
    assert fresh.transfer.transfer_type == "L"


def test_cleanup_task_returns_a_stuck_upload_to_pending(
    file_service,
    location,
    example_file_record,
    identity_simple,
    db,
    set_app_config_fn_scoped,
):
    """An upload that could not finish becomes pending again, not a broken row."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    recid = example_file_record["id"]
    file_service.init_files(identity_simple, recid, [{"key": "stuck.bin"}])

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    claim = FileUpload(file_service)._prepare(record, "stuck.bin", content_length=4)
    claim.storage.save(BytesIO(b"gone"), size=4)

    # The record still points at the reserved row, so the row cannot be deleted.
    cleanup_failed_upload(str(claim.file_instance_id), claim.uri)

    file_instance = db.session.get(FileInstance, claim.file_instance_id)
    assert file_instance is not None
    assert file_instance.uri is None
    assert file_instance.readable is False
    assert file_instance.writable is True

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert record.files["stuck.bin"].object_version.file_id == claim.file_instance_id

    # Pending again, so the same key can be uploaded.
    result = file_service.set_file_content(
        identity_simple, recid, "stuck.bin", BytesIO(b"redo"), 4
    )
    assert result.errors is None
    file_service.commit_file(identity_simple, recid, "stuck.bin")
    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert record.files["stuck.bin"].object_version.file.readable is True


def test_remote_files_count_towards_total_bytes(
    file_service,
    example_file_record,
    identity_simple,
    location,
):
    """A remote file has content even though it cannot be read from here."""
    recid = example_file_record["id"]
    file_service.init_files(
        identity_simple,
        recid,
        [
            {
                "key": "remote.txt",
                "checksum": "md5:c785060c866796cc2a1708c997154c8e",
                "size": 17,
                "transfer": {
                    "url": "https://inveniordm.test/files/remote.txt",
                    "type": "R",
                },
            }
        ],
    )

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    file_record = record.files["remote.txt"]
    assert file_record.is_readable is False
    assert file_record.has_content is True
    assert record.files.total_bytes == 17
    assert record.files.mimetypes == ["text/plain"]
    assert record.files.exts == ["txt"]


def test_reserved_uploads_do_not_count_towards_total_bytes(
    file_service,
    location,
    example_file_record,
    identity_simple,
    set_app_config_fn_scoped,
):
    """A file still being uploaded has no content yet."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    recid = example_file_record["id"]
    file_service.init_files(identity_simple, recid, [{"key": "pending.bin"}])

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert record.files["pending.bin"].has_content is False
    assert record.files.total_bytes == 0

    claim = FileUpload(file_service)._prepare(record, "pending.bin", content_length=4)

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert record.files["pending.bin"].has_content is False
    assert record.files.total_bytes == 0

    # Back to pending, so the same key can be uploaded.
    claim.discard()

    file_service.set_file_content(
        identity_simple, recid, "pending.bin", BytesIO(b"done"), 4
    )
    file_service.commit_file(identity_simple, recid, "pending.bin")

    record = file_service.record_cls.pid.resolve(recid, registered_only=False)
    assert record.files["pending.bin"].has_content is True
    assert record.files.total_bytes == 4
