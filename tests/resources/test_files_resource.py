# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs"""

from io import BytesIO

import pytest
from mock_module.resource import CustomFileActionResource, \
    CustomFileResource, CustomRecordResource
from mock_module.service import FileService


@pytest.fixture(scope="module")
def record_resource():
    """Record Resource."""
    return CustomRecordResource(service=FileService())


@pytest.fixture(scope="module")
def file_resources():
    """File Resources."""
    return {
        'mock_file': CustomFileResource(service=FileService()),
        'mock_file_action': CustomFileActionResource(service=FileService()),
    }


@pytest.fixture(scope="module")
def base_app(base_app, file_resources):
    """Application factory fixture."""
    for name, resource in file_resources.items():
        base_app.register_blueprint(resource.as_blueprint(name))
    yield base_app


def test_files_api_flow(app, client, es_clear, headers, location):
    """Test record creation."""
    # Initialize a draft
    res = client.post('/mocks', headers=headers)
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


def test_default_preview_file(app, client, es_clear, headers, location):
    # Initialize a draft
    res = client.post('/mocks', headers=headers)
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


def test_enabled_files(app, client, es_clear, headers, location):
    # Initialize a draft
    res = client.post('/mocks', headers=headers)
    assert res.status_code == 201
    id_ = res.json['id']
    assert res.json['links']['files'].endswith(f'/api/mocks/{id_}/files')

    # Get all files and check "enabled"
    res = client.get(f"/mocks/{id_}/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json['entries']) == 0
    assert res.json['enabled'] is True

    # Disable files
    res = client.put(f"/mocks/{id_}/files", headers=headers, json={
        'enabled': False
    })
    assert res.status_code == 200
    assert res.json['enabled'] is False
    assert 'self' in res.json['links']
    assert 'entries' not in res.json
    assert 'default_preview' not in res.json
    assert 'order' not in res.json

    # Enable again
    res = client.put(f"/mocks/{id_}/files", headers=headers, json={
        'enabled': True
    })
    assert res.status_code == 200
    assert res.json['enabled'] is True
    assert 'self' in res.json['links']
    assert len(res.json['entries']) == 0
    assert res.json['default_preview'] is None
    assert res.json['order'] == []

    # Initialize 3 files
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

    # Get all files
    res = client.get(f"/mocks/{id_}/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json['entries']) == 3
    assert res.json['enabled'] is True

    # Disable files
    res = client.put(f"/mocks/{id_}/files", headers=headers, json={
        'enabled': False
    })
    assert res.status_code == 200
    assert res.json['enabled'] is False
    assert 'self' in res.json['links']
    assert 'entries' not in res.json
    assert 'default_preview' not in res.json
    assert 'order' not in res.json

    # Enable files again
    res = client.put(f"/mocks/{id_}/files", headers=headers, json={
        'enabled': True
    })
    assert res.status_code == 200
    assert res.json['enabled'] is True
    assert 'self' in res.json['links']
    assert len(res.json['entries']) == 0
    assert res.json['default_preview'] is None
    assert res.json['order'] == []
