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
    CustomFileActionResourceConfig, CustomFileResource, \
    CustomFileResourceConfig, CustomRecordResource, \
    CustomRecordResourceConfig
from mock_module.service import FileServiceConfig, Service


@pytest.fixture(scope="module")
def record_resource():
    """Record Resource."""
    return CustomRecordResource(
        config=CustomRecordResourceConfig,
        service=Service(config=FileServiceConfig)
    )


@pytest.fixture(scope="module")
def file_resources():
    """File Resources."""
    return {
        'mock_file': CustomFileResource(
            config=CustomFileResourceConfig,
            service=Service(config=FileServiceConfig)
        ),
        'mock_file_action': CustomFileActionResource(
            config=CustomFileActionResourceConfig,
            service=Service(config=FileServiceConfig)
        ),
    }


@pytest.fixture(scope="module")
def base_app(base_app, file_resources):
    """Application factory fixture."""
    for name, resource in file_resources.items():
        base_app.register_blueprint(resource.as_blueprint(name))
    yield base_app


def test_status_codes(app, client, es_clear, headers, location):
    """Test record creation."""
    # Initialize a draft
    res = client.post('/mocks', headers=headers)
    assert res.status_code == 201
    id_ = res.json['id']

    # Initialize files upload
    res = client.post(f'/mocks/{id_}/files', headers=headers, json=[
        {'key': 'test.pdf', 'title': 'Test file'},
    ])
    assert res.status_code == 201
    assert res.json['entries'][0]['key'] == 'test.pdf'
    assert res.json['entries'][0]['metadata'] == {'title': 'Test file'}

    # Get the file metadata
    res = client.get(f"/mocks/{id_}/files/test.pdf", headers=headers)
    assert res.status_code == 200
    assert res.json['key'] == 'test.pdf'
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

    # Commit the uploaded file
    res = client.post(f"/mocks/{id_}/files/test.pdf/commit", headers=headers)
    assert res.status_code == 200

    # Get the file metadata
    res = client.get(f"/mocks/{id_}/files/test.pdf", headers=headers)
    assert res.status_code == 200
    assert res.json['key'] == 'test.pdf'
    assert res.json['metadata'] == {'title': 'Test file'}
    print(res.json)

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
    assert res.json['metadata'] == {'title': 'New title'}

    # Get all files
    res = client.get(f"/mocks/{id_}/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json['entries']) == 1
    assert res.json['entries'][0]['key'] == 'test.pdf'
    assert res.json['entries'][0]['metadata'] == {'title': 'New title'}

    # Delete a file
    res = client.delete(f"/mocks/{id_}/files/test.pdf", headers=headers)
    assert res.status_code == 204

    # Get all files
    res = client.get(f"/mocks/{id_}/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json['entries']) == 0
