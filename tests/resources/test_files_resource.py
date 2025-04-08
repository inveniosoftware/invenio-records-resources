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

"""Invenio Resources module to create REST APIs."""

import zipfile
from io import BytesIO
from unittest.mock import patch

import pytest
from zipstream import ZipStream

from tests.mock_module import service_for_files, service_for_records_w_files


@pytest.fixture(scope="module")
def extra_entry_points():
    """Extra entry points to load the mock_module features."""
    return {
        "invenio_db.model": [
            "mock_module = tests.mock_module.models",
        ],
        "invenio_jsonschemas.schemas": [
            "mock_module = tests.mock_module.jsonschemas",
        ],
        "invenio_search.mappings": [
            "records = tests.mock_module.mappings",
        ],
        "invenio_base.api_blueprints": [
            "mock_module_mocks = tests.mock_module:create_mocks_w_files_bp",
            "mock_module_mocks_files = tests.mock_module:create_mocks_files_bp",
            "mock_module_mocks_files_disabled_upload = tests.mock_module:create_mocks_files_disabled_upload_bp",
        ],
    }


@pytest.fixture(scope="module")
def base_app(
    base_app,
):
    """Application factory fixture."""
    registry = base_app.extensions["invenio-records-resources"].registry
    registry.register(service_for_records_w_files, service_id="mock-records")
    registry.register(service_for_files, service_id="mock-files")
    yield base_app


@pytest.fixture()
def input_data(input_data):
    input_data["files"] = {"enabled": True}
    return input_data


def test_files_api_flow(client, search_clear, headers, input_data, location):
    """Test record creation."""
    # Initialize a draft
    res = client.post("/mocks", headers=headers, json=input_data)
    assert res.status_code == 201
    id_ = res.json["id"]
    assert res.json["links"]["files"].endswith(f"/api/mocks/{id_}/files")

    # Initialize files upload
    res = client.post(
        f"/mocks/{id_}/files",
        headers=headers,
        json=[
            {"key": "test.pdf", "metadata": {"title": "Test file"}},
        ],
    )
    assert res.status_code == 201
    res_file = res.json["entries"][0]
    assert res_file["key"] == "test.pdf"
    assert res_file["status"] == "pending"
    assert res_file["metadata"] == {"title": "Test file"}
    assert res_file["links"]["self"].endswith(f"/api/mocks/{id_}/files/test.pdf")
    assert res_file["links"]["content"].endswith(
        f"/api/mocks/{id_}/files/test.pdf/content"
    )
    assert res_file["links"]["commit"].endswith(
        f"/api/mocks/{id_}/files/test.pdf/commit"
    )

    # Get the file metadata
    res = client.get(f"/mocks/{id_}/files/test.pdf", headers=headers)
    assert res.status_code == 200
    assert res.json["key"] == "test.pdf"
    assert res.json["status"] == "pending"
    assert res.json["metadata"] == {"title": "Test file"}

    # Upload a file
    res = client.put(
        f"/mocks/{id_}/files/test.pdf/content",
        headers={
            "content-type": "application/octet-stream",
            "accept": "application/json",
        },
        data=BytesIO(b"testfile"),
    )
    assert res.status_code == 200
    assert res.json["status"] == "pending"

    # Commit the uploaded file
    res = client.post(f"/mocks/{id_}/files/test.pdf/commit", headers=headers)
    assert res.status_code == 200
    assert res.json["status"] == "completed"

    # Get the file metadata
    res = client.get(f"/mocks/{id_}/files/test.pdf", headers=headers)
    assert res.status_code == 200
    assert res.json["key"] == "test.pdf"
    assert res.json["status"] == "completed"
    assert res.json["metadata"] == {"title": "Test file"}
    assert isinstance(res.json["size"], int), "File size not integer"

    # Read a file's content
    res = client.get(f"/mocks/{id_}/files/test.pdf/content", headers=headers)
    assert res.status_code == 200
    assert res.data == b"testfile"

    # Update file metadata
    res = client.put(
        f"/mocks/{id_}/files/test.pdf",
        headers=headers,
        json={"metadata": {"title": "New title"}},
    )
    assert res.status_code == 200
    assert res.json["key"] == "test.pdf"
    assert res.json["status"] == "completed"
    assert res.json["metadata"] == {"title": "New title"}

    # Get all files
    res = client.get(f"/mocks/{id_}/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json["entries"]) == 1
    assert res.json["entries"][0]["key"] == "test.pdf"
    assert res.json["entries"][0]["status"] == "completed"
    assert res.json["entries"][0]["metadata"] == {"title": "New title"}

    # Delete a file
    res = client.delete(f"/mocks/{id_}/files/test.pdf", headers=headers)
    assert res.status_code == 204

    # Get all files
    res = client.get(f"/mocks/{id_}/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json["entries"]) == 0


def test_empty_file(client, search_clear, headers, input_data, location):
    """Test if an empty file works properly."""
    # Initialize a draft
    res = client.post("/mocks", headers=headers, json=input_data)
    assert res.status_code == 201
    id_ = res.json["id"]
    assert res.json["links"]["files"].endswith(f"/api/mocks/{id_}/files")

    # Initialize files upload
    res = client.post(
        f"/mocks/{id_}/files",
        headers=headers,
        json=[
            {"key": "empty", "metadata": {"title": "Zero-length test file"}},
        ],
    )
    assert res.status_code == 201

    # Upload the empty file
    res = client.put(
        f"/mocks/{id_}/files/empty/content",
        headers={
            "content-type": "application/octet-stream",
            "accept": "application/json",
        },
        data=BytesIO(b""),
    )
    assert res.status_code == 200

    # Commit the uploaded file
    res = client.post(f"/mocks/{id_}/files/empty/commit", headers=headers)
    assert res.status_code == 200

    # Get the file metadata, check if everything (especially size) is present
    res = client.get(f"/mocks/{id_}/files/empty", headers=headers)
    assert res.status_code == 200
    assert res.json["key"] == "empty"
    assert res.json["checksum"] == "md5:d41d8cd98f00b204e9800998ecf8427e"
    assert res.json["size"] == 0

    # Read a file's content
    res = client.get(f"/mocks/{id_}/files/empty/content", headers=headers)
    assert res.status_code == 200
    assert res.data == b""


def test_default_preview_file(app, client, search_clear, headers, input_data, location):
    # Initialize a draft
    res = client.post("/mocks", headers=headers, json=input_data)
    assert res.status_code == 201
    id_ = res.json["id"]
    assert res.json["links"]["files"].endswith(f"/api/mocks/{id_}/files")

    # Initialize 3 file uploads
    res = client.post(
        f"/mocks/{id_}/files",
        headers=headers,
        json=[
            {"key": "f1.pdf"},
            {"key": "f2.pdf"},
            {"key": "f3.pdf"},
        ],
    )
    assert res.status_code == 201
    file_entries = res.json["entries"]
    assert len(file_entries) == 3
    assert {(f["key"], f["status"]) for f in file_entries} == {
        ("f1.pdf", "pending"),
        ("f2.pdf", "pending"),
        ("f3.pdf", "pending"),
    }
    assert res.json["default_preview"] is None

    # Upload and commit the 3 files
    for f in file_entries:
        res = client.put(
            f"/mocks/{id_}/files/{f['key']}/content",
            headers={
                "content-type": "application/octet-stream",
                "accept": "application/json",
            },
            data=BytesIO(b"testfile"),
        )
        assert res.status_code == 200
        assert res.json["status"] == "pending"

        res = client.post(f"/mocks/{id_}/files/{f['key']}/commit", headers=headers)
        assert res.status_code == 200
        assert res.json["status"] == "completed"

    # Set the default preview file
    input_data["files"]["default_preview"] = "f1.pdf"
    res = client.put(f"/mocks/{id_}", headers=headers, json=input_data)
    assert res.status_code == 200
    assert res.json["files"]["default_preview"] == "f1.pdf"

    # Change the default preview file
    input_data["files"]["default_preview"] = "f2.pdf"
    res = client.put(f"/mocks/{id_}", headers=headers, json=input_data)
    assert res.status_code == 200
    assert res.json["files"]["default_preview"] == "f2.pdf"

    # Unset the default preview file
    input_data["files"]["default_preview"] = None
    res = client.put(f"/mocks/{id_}", headers=headers, json=input_data)
    assert res.status_code == 200
    assert res.json["files"].get("default_preview") is None

    # Empty string the default preview file
    input_data["files"]["default_preview"] = ""
    res = client.put(f"/mocks/{id_}", headers=headers, json=input_data)
    assert res.status_code == 200
    assert res.json["files"].get("default_preview") is None

    # Set the default preview file
    input_data["files"]["default_preview"] = "f3.pdf"
    res = client.put(f"/mocks/{id_}", headers=headers, json=input_data)
    assert res.status_code == 200
    assert res.json["files"]["default_preview"] == "f3.pdf"

    # Delete the default preview file
    res = client.delete(f"/mocks/{id_}/files/f3.pdf", headers=headers)
    assert res.status_code == 204

    # Get all files and check default preview
    res = client.get(f"/mocks/{id_}/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json["entries"]) == 2
    assert res.json["default_preview"] is None


def test_file_api_errors(client, search_clear, headers, input_data, location):
    """Test REST API errors for file management."""
    h = headers

    # Initialize a draft
    res = client.post("/mocks", headers=headers, json=input_data)
    assert res.status_code == 201
    id_ = res.json["id"]
    assert res.json["links"]["files"].endswith(f"/api/mocks/{id_}/files")

    # Initialize files upload
    # Pass an object instead of an array
    res = client.post(f"/mocks/{id_}/files", headers=headers, json={"key": "test.pdf"})
    assert res.status_code == 400
    assert res.json == {
        "errors": [{"field": "0._schema", "messages": ["Invalid input type."]}],
        "message": "A validation error occurred.",
        "status": 400,
    }

    res = client.post(
        f"/mocks/{id_}/files",
        headers=headers,
        json=[{"key": "test.pdf", "transfer": "not a dictionary"}],
    )
    assert res.status_code == 400
    assert res.json == {
        "errors": [
            {
                "field": "transfer",
                "messages": ["Transfer metadata must be a dictionary."],
            }
        ],
        "message": "A validation error occurred.",
        "status": 400,
    }

    res = client.post(
        f"/mocks/{id_}/files",
        headers=headers,
        json=[
            {"key": "test.pdf", "metadata": {"title": "Test file"}},
        ],
    )
    assert res.status_code == 201

    # Upload a file
    res = client.put(
        f"/mocks/{id_}/files/test.pdf/content",
        headers={
            "content-type": "application/octet-stream",
            "accept": "application/json",
        },
        data=BytesIO(b"testfile"),
    )
    assert res.status_code == 200
    assert res.json["status"] == "pending"

    # Commit the uploaded file
    res = client.post(f"/mocks/{id_}/files/test.pdf/commit", headers=headers)
    assert res.status_code == 200
    assert res.json["status"] == "completed"

    # Initialize same file upload again
    res = client.post(
        f"/mocks/{id_}/files",
        headers=headers,
        json=[
            {"key": "test.pdf", "metadata": {"title": "Test file"}},
        ],
    )
    assert res.status_code == 400
    assert res.json == {
        "message": "File with key test.pdf already exists.",
        "status": 400,
    }


def test_disabled_upload_file_resource(
    client, search_clear, headers, input_data, location
):
    """Test file resources with disabled file upload"""

    # Initialize a draft
    res = client.post("/mocks", headers=headers, json=input_data)
    assert res.status_code == 201
    id_ = res.json["id"]

    # File manipulation api should not be exposed if allow_upload is disabled
    res = client.post(
        f"/mocks_disabled_files_upload/{id_}/files",
        headers=headers,
        json=[{"key": "test.pdf", "title": "Test file"}],
    )
    assert res.status_code == 405

    res = client.put(
        f"/mocks_disabled_files_upload/{id_}/files",
        headers=headers,
        json=[{"default_preview": "test.pdf"}],
    )
    assert res.status_code == 405

    res = client.delete(
        f"/mocks_disabled_files_upload/{id_}/files/test.pdf", headers=headers
    )
    assert res.status_code == 405


def test_disable_files_when_files_already_present_should_error(
    app, client, search_clear, headers, input_data, location
):
    # Initialize a record
    response = client.post("/mocks", headers=headers, json=input_data)
    id_ = response.json["id"]
    # Add file
    file_id = "f1.pdf"
    client.post(f"/mocks/{id_}/files", headers=headers, json=[{"key": file_id}])
    client.put(
        f"/mocks/{id_}/files/{file_id}/content",
        headers={
            "content-type": "application/octet-stream",
            "accept": "application/json",
        },
        data=BytesIO(b"testfile"),
    )
    client.post(f"/mocks/{id_}/files/{file_id}/commit", headers=headers)
    # Disable files
    input_data["files"] = {"enabled": False}

    response = client.put(f"/mocks/{id_}", headers=headers, json=input_data)

    assert response.status_code == 400
    assert response.json["errors"] == [
        {
            "field": "files.enabled",
            "messages": [
                "You must first delete all files to set the record to be "
                "metadata-only."
            ],
        }
    ]


def test_download_archive(
    app,
    client,
    search_clear,
    headers,
    input_data,
    location,
):
    # Initialize a draft
    res = client.post("/mocks", headers=headers, json=input_data)
    assert res.status_code == 201
    id_ = res.json["id"]
    assert res.json["links"]["files"].endswith(f"/api/mocks/{id_}/files")

    # Initialize 3 file uploads
    res = client.post(
        f"/mocks/{id_}/files",
        headers=headers,
        json=[
            {"key": "f1.pdf"},
            {"key": "f2.pdf"},
            {"key": "f3.pdf"},
        ],
    )
    assert res.status_code == 201
    file_entries = res.json["entries"]
    assert len(file_entries) == 3
    assert {(f["key"], f["status"]) for f in file_entries} == {
        ("f1.pdf", "pending"),
        ("f2.pdf", "pending"),
        ("f3.pdf", "pending"),
    }

    # Upload and commit the 3 files
    for f in file_entries:
        res = client.put(
            f"/mocks/{id_}/files/{f['key']}/content",
            headers={
                "content-type": "application/octet-stream",
                "accept": "application/json",
            },
            data=BytesIO(b"testfile"),
        )
        assert res.status_code == 200
        assert res.json["status"] == "pending"

        res = client.post(f"/mocks/{id_}/files/{f['key']}/commit", headers=headers)
        assert res.status_code == 200
        assert res.json["status"] == "completed"

    captured_fps = []

    class MockZipStream(ZipStream):
        def add(self, fp, *args, **kwargs):
            # Keep track of all passed file pointers
            captured_fps.append(fp)
            return super().add(fp, *args, **kwargs)

    # Get all files as zipped archive
    with patch(
        "invenio_records_resources.resources.files.resource.ZipStream",
        new=MockZipStream,
    ):
        res = client.get(
            f"/mocks/{id_}/files-archive",
        )
        assert res.status_code == 200
        res_bytes = BytesIO(res.data)
        with zipfile.ZipFile(res_bytes, "r") as zf:
            files = zf.namelist()
            files.sort()
            assert files == ["f1.pdf", "f2.pdf", "f3.pdf"]
    assert all(f.closed for f in captured_fps)


def test_files_multipart_api_flow(
    app, client, search_clear, headers, input_data, location
):
    """Test record creation."""
    # Initialize a draft
    res = client.post("/mocks", headers=headers, json=input_data)
    assert res.status_code == 201
    id_ = res.json["id"]
    assert res.json["links"]["files"].endswith(f"/api/mocks/{id_}/files")

    # Initialize files upload
    res = client.post(
        f"/mocks/{id_}/files",
        headers=headers,
        json=[
            {
                "key": "test.pdf",
                "metadata": {
                    "title": "Test file",
                },
                "size": 17,
                "transfer": {
                    "type": "M",
                    "parts": 2,
                    "part_size": 10,
                },
            },
        ],
    )
    assert res.status_code == 201
    res_file = res.json["entries"][0]
    assert res_file["key"] == "test.pdf"
    assert res_file["status"] == "pending"
    assert res_file["metadata"] == {"title": "Test file"}
    assert res_file["links"]["self"].endswith(f"/api/mocks/{id_}/files/test.pdf")
    assert "content" not in res_file["links"]
    assert res_file["links"]["commit"].endswith(
        f"/api/mocks/{id_}/files/test.pdf/commit"
    )

    parts_links = {
        x["part"]: x["url"].split("/api", maxsplit=1)[1]
        for x in res_file["links"]["parts"]
    }

    assert len(parts_links) == 2

    def upload_part(part_number, data):
        res = client.put(
            parts_links[part_number],
            headers={
                "content-type": "application/octet-stream",
            },
            data=data,
        )
        assert res.status_code == 200
        assert res.json["status"] == "pending"
        assert res.json["transfer"]["type"] == "M"

    upload_part(1, b"1234567890")
    upload_part(2, b"1234567")

    # Commit the uploaded file
    res = client.post(f"/mocks/{id_}/files/test.pdf/commit", headers=headers)
    assert res.status_code == 200
    assert res.json["status"] == "completed"
    assert res.json["transfer"]["type"] == "L"

    # Get the file metadata
    res = client.get(f"/mocks/{id_}/files/test.pdf", headers=headers)
    assert res.status_code == 200
    assert res.json["key"] == "test.pdf"
    assert res.json["status"] == "completed"
    assert res.json["metadata"] == {"title": "Test file"}
    assert isinstance(res.json["size"], int), "File size not integer"

    # Read a file's content
    res = client.get(f"/mocks/{id_}/files/test.pdf/content", headers=headers)
    assert res.status_code == 200
    assert res.data == b"12345678901234567"
