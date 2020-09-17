# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests."""

import json

import pytest
from invenio_search import current_search, current_search_client


@pytest.fixture()
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        'metadata': {
            'title': 'Test'
        },
    }


@pytest.fixture()
def headers():
    """Default headers for making requests."""
    return {
        'content-type': 'application/json',
        'accept': 'application/json',
    }


def test_simple_flow(app, client, input_data, headers):
    """Test a simple REST API flow."""
    idx = 'records-record-v1.0.0'
    h = headers

    # Create a record
    res = client.post('/mocks', headers=h, data=json.dumps(input_data))
    assert res.status_code == 201
    id_ = res.json['id']
    assert res.json['metadata'] == input_data['metadata']

    # Read the record
    res = client.get(f'/mocks/{id_}', headers=h)
    assert res.status_code == 200
    assert res.json['metadata'] == input_data['metadata']

    # TODO: Should this be part of the service? we don't know the index easily
    current_search.flush_and_refresh(idx)

    # Search it
    res = client.get(f'/mocks', query_string={'q': f'id:{id_}'}, headers=h)
    assert res.status_code == 200
    assert res.json['hits']['total'] == 1
    assert res.json['hits']['hits'][0]['metadata'] == input_data['metadata']
    print(res.json)

    # Delete it
    res = client.delete(f'/mocks/{id_}')
    assert res.status_code == 204
    assert res.get_data(as_text=True) == ''

    current_search.flush_and_refresh(idx)

    # Try to get it again
    res = client.get(f'/mocks/{id_}', headers=h)
    assert res.status_code == 410

    # Try to get search it again
    res = client.get(f'/mocks', query_string={'q': f'id:{id_}'}, headers=h)
    assert res.status_code == 200
    assert res.json['hits']['total'] == 0
