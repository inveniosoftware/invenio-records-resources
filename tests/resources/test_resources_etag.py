# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resources etag test."""

import json

import pytest


@pytest.fixture()
def input_data(client, headers):
    """Input data (as coming from the view layer)."""
    data = {
        'metadata': {
            'title': 'Test'
        },
    }
    res = client.post('/mocks', headers=headers, data=json.dumps(data))
    assert res.status_code == 201
    return res.json


def test_etag_update(app, client, input_data, headers):
    """Test a simple REST API flow."""
    id_ = input_data["id"]
    revision_id = input_data["revision_id"]

    # Update with outdated etag version
    headers.update(dict(if_match=100))
    res = client.put(
        f'/mocks/{id_}', headers=headers, data=json.dumps(input_data))
    assert res.status_code == 412

    # Update with correct etag version
    headers.update(dict(if_match=revision_id))
    res = client.put(
        f'/mocks/{id_}', headers=headers, data=json.dumps(input_data))
    assert res.status_code == 200


def test_etag_delete(app, client, input_data, headers):
    """Test a simple REST API flow."""
    id_ = input_data["id"]
    revision_id = input_data["revision_id"]

    # Delete with outdated etag version
    headers.update(dict(if_match=100))
    res = client.delete(f'/mocks/{id_}', headers=headers)
    assert res.status_code == 412

    # Delete with correct etag version
    headers.update(dict(if_match=revision_id))
    res = client.delete(f'/mocks/{id_}', headers=headers)
    assert res.status_code == 204
