# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from io import BytesIO

import pytest
from mock_module.config import ServiceWithFilesConfig
from mock_module.resource import CustomDisabledUploadFileResourceConfig, \
    CustomFileResourceConfig, CustomRecordResourceConfig

from invenio_records_resources.resources import FileResource, RecordResource
from invenio_records_resources.services import RecordService


@pytest.fixture(scope="module")
def service():
    return RecordService(ServiceWithFilesConfig)


@pytest.fixture(scope="module")
def record_resource(service):
    """Record Resource."""
    return RecordResource(CustomRecordResourceConfig, service)


@pytest.fixture(scope="module")
def file_resource(file_service):
    """File Resources."""
    return FileResource(CustomFileResourceConfig, file_service)


@pytest.fixture(scope="module")
def disabled_file_upload_resource(file_service):
    """Disabled Upload File Resource."""
    return FileResource(CustomDisabledUploadFileResourceConfig, file_service)


@pytest.fixture(scope="module")
def base_app(base_app, file_resource, disabled_file_upload_resource):
    """Application factory fixture."""
    base_app.register_blueprint(file_resource.as_blueprint())
    base_app.register_blueprint(disabled_file_upload_resource.as_blueprint())
    yield base_app


@pytest.fixture()
def input_data(input_data):
    input_data["files"] = {
        'enabled': True
    }
    return input_data


def test_files_api_flow(client, es_clear, headers, input_data, location):
    """Test record creation."""
    # Initialize a draft
    res = client.post('/mocks', headers=headers, json=input_data)
    assert res.status_code == 201
    id_ = res.json['id']
    assert res.json['links']['files'].endswith(f'/api/mocks/{id_}/files')

    # Initialize files upload
    res = client.post(f'/mocks/{id_}/files', headers=headers, json=[
        {'key': 'test.pdf', 'title': 'Test file'},
    ])
    assert res.status_code == 201
    res_file = res.json['entries'][0]
    assert res_file['key'] == 'test.pdf'
    assert res_file['status'] == 'pending'
    assert res_file['metadata'] == {'title': 'Test file'}
    assert res_file['links']['self'].endswith(
        f'/api/mocks/{id_}/files/test.pdf')
    assert res_file['links']['content'].endswith(
        f'/api/mocks/{id_}/files/test.pdf/content')
    assert res_file['links']['commit'].endswith(
        f'/api/mocks/{id_}/files/test.pdf/commit')

    # Get the file metadata
    res = client.get(f"/mocks/{id_}/files/test.pdf", headers=headers)
    assert res.status_code == 200
    assert res.json['key'] == 'test.pdf'
    assert res.json['status'] == 'pending'
    assert res.json['metadata'] == {'title': 'Test file'}

    # Upload a file
    res = client.put(
        f"/mocks/{id_}/files/test.pdf/content", headers={
            'content-type': 'application/octet-stream',
            'accept': 'application/json',
        },
        data=BytesIO(b'testfile'),
    )
    assert res.status_code == 200
    assert res.json['status'] == 'pending'

    # Commit the uploaded file
    res = client.post(f"/mocks/{id_}/files/test.pdf/commit", headers=headers)
    assert res.status_code == 200
    assert res.json['status'] == 'completed'

    # Get the file metadata
    res = client.get(f"/mocks/{id_}/files/test.pdf", headers=headers)
    assert res.status_code == 200
    assert res.json['key'] == 'test.pdf'
    assert res.json['status'] == 'completed'
    assert res.json['metadata'] == {'title': 'Test file'}

    # Read a file's content
    res = client.get(f"/mocks/{id_}/files/test.pdf/content", headers=headers)
    assert res.status_code == 200
    assert res.data == b'testfile'

    # Update file metadata
    res = client.put(
        f"/mocks/{id_}/files/test.pdf", headers=headers,
        json={'title': 'New title'})
    assert res.status_code == 200
    assert res.json['key'] == 'test.pdf'
    assert res.json['status'] == 'completed'
    assert res.json['metadata'] == {'title': 'New title'}

    # Get all files
    res = client.get(f"/mocks/{id_}/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json['entries']) == 1
    assert res.json['entries'][0]['key'] == 'test.pdf'
    assert res.json['entries'][0]['status'] == 'completed'
    assert res.json['entries'][0]['metadata'] == {'title': 'New title'}

    # Delete a file
    res = client.delete(f"/mocks/{id_}/files/test.pdf", headers=headers)
    assert res.status_code == 204

    # Get all files
    res = client.get(f"/mocks/{id_}/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json['entries']) == 0


def test_default_preview_file(
        app, client, es_clear, headers, input_data, location):
    # Initialize a draft
    res = client.post('/mocks', headers=headers, json=input_data)
    assert res.status_code == 201
    id_ = res.json['id']
    assert res.json['links']['files'].endswith(f'/api/mocks/{id_}/files')

    # Initialize 3 file uploads
    res = client.post(f'/mocks/{id_}/files', headers=headers, json=[
        {'key': 'f1.pdf'},
        {'key': 'f2.pdf'},
        {'key': 'f3.pdf'},
    ])
    assert res.status_code == 201
    file_entries = res.json['entries']
    assert len(file_entries) == 3
    assert {(f['key'], f['status']) for f in file_entries} == {
        ('f1.pdf', 'pending'),
        ('f2.pdf', 'pending'),
        ('f3.pdf', 'pending'),
    }
    assert res.json['default_preview'] is None

    # Upload and commit the 3 files
    for f in file_entries:
        res = client.put(
            f"/mocks/{id_}/files/{f['key']}/content", headers={
                'content-type': 'application/octet-stream',
                'accept': 'application/json',
            },
            data=BytesIO(b'testfile'),
        )
        assert res.status_code == 200
        assert res.json['status'] == 'pending'

        res = client.post(
            f"/mocks/{id_}/files/{f['key']}/commit", headers=headers)
        assert res.status_code == 200
        assert res.json['status'] == 'completed'

    # Set the default preview file
    res = client.put(f"/mocks/{id_}/files", headers=headers, json={
        'default_preview': 'f1.pdf'
    })
    assert res.status_code == 200
    assert res.json['default_preview'] == 'f1.pdf'

    # Change the default preview file
    res = client.put(f"/mocks/{id_}/files", headers=headers, json={
        'default_preview': 'f2.pdf'
    })
    assert res.status_code == 200
    assert res.json['default_preview'] == 'f2.pdf'

    # Unset the default preview file
    res = client.put(f"/mocks/{id_}/files", headers=headers, json={
        'default_preview': None
    })
    assert res.status_code == 200
    assert res.json['default_preview'] is None

    # Set the default preview file
    res = client.put(f"/mocks/{id_}/files", headers=headers, json={
        'default_preview': 'f3.pdf'
    })
    assert res.status_code == 200
    assert res.json['default_preview'] == 'f3.pdf'

    # Delete the default preview file
    res = client.delete(f"/mocks/{id_}/files/f3.pdf", headers=headers, json={
        'default_preview': 'f3.pdf'
    })
    assert res.status_code == 204

    # Get all files and check default preview
    res = client.get(f"/mocks/{id_}/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json['entries']) == 2
    assert res.json['default_preview'] is None


def test_file_api_errors(client, es_clear, headers, input_data, location):
    """Test REST API errors for file management."""
    h = headers

    # Initialize a draft
    res = client.post('/mocks', headers=headers, json=input_data)
    assert res.status_code == 201
    id_ = res.json['id']
    assert res.json['links']['files'].endswith(f'/api/mocks/{id_}/files')

    # Initialize files upload
    res = client.post(f'/mocks/{id_}/files', headers=headers, json=[
        {'key': 'test.pdf', 'title': 'Test file'},
    ])
    assert res.status_code == 201
    res_file = res.json['entries'][0]

    # Upload a file
    res = client.put(
        f"/mocks/{id_}/files/test.pdf/content", headers={
            'content-type': 'application/octet-stream',
            'accept': 'application/json',
        },
        data=BytesIO(b'testfile'),
    )
    assert res.status_code == 200
    assert res.json['status'] == 'pending'

    # Commit the uploaded file
    res = client.post(f"/mocks/{id_}/files/test.pdf/commit", headers=headers)
    assert res.status_code == 200
    assert res.json['status'] == 'completed'

    # Initialize same file upload again
    res = client.post(f'/mocks/{id_}/files', headers=headers, json=[
        {'key': 'test.pdf', 'title': 'Test file'},
    ])
    assert res.status_code == 400


def test_disabled_upload_file_resource(
        client, es_clear, headers, input_data, location):
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
        app, client, es_clear, headers, input_data, location):
    # Initialize a record
    response = client.post('/mocks', headers=headers, json=input_data)
    id_ = response.json["id"]
    # Add file
    file_id = 'f1.pdf'
    client.post(
        f'/mocks/{id_}/files',
        headers=headers,
        json=[{'key': file_id}]
    )
    client.put(
        f"/mocks/{id_}/files/{file_id}/content",
        headers={
            'content-type': 'application/octet-stream',
            'accept': 'application/json',
        },
        data=BytesIO(b'testfile'),
    )
    client.post(f"/mocks/{id_}/files/{file_id}/commit", headers=headers)
    # Disable files
    input_data["files"] = {
        'enabled': False
    }

    response = client.put(f"/mocks/{id_}", headers=headers, json=input_data)

    assert response.status_code == 400
    assert response.json["errors"] == [
        {
            'field': 'files.enabled',
            'messages': [
                "You must first delete all files to set the record to be "
                "metadata-only."
            ]
        }
    ]
