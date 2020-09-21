# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests.

Test to add:
- Read a tombstone page
- Read with missing permissions
- Read with missing pid
"""

import pytest
from invenio_search import current_search
from marshmallow import ValidationError


#
# Helpers
#
def order(res_dict):
    """Assert the order of records in a search result."""
    return [int(h['metadata']['title']) for h in res_dict['hits']['hits']]


def sort_method(res):
    """Get the sort method from a result."""
    return res['links']['self']['params']['sort']


#
# Fixtures
#
@pytest.fixture(scope='module')
def records(app, service, identity_simple):
    """Input data (as coming from the view layer)."""
    items = []
    for idx in range(3):
        data = {
           'metadata': {
                'title': f'00{idx}'
            },
        }
        items.append(service.create(identity_simple, data))
    current_search.flush_and_refresh('records-record-v1.0.0')
    return items


#
# Tests
#
def test_default_no_query(service, identity_simple, records):
    """Default sorting without a query."""
    res = service.search(
        identity_simple, page=1, size=10, _max_results=100).to_dict()
    assert sort_method(res) == 'mostrecent'


def test_default_with_query(service, identity_simple, records):
    """Default sorting without a query."""
    res = service.search(
        identity_simple, q='test', page=1, size=10, _max_results=100).to_dict()
    assert sort_method(res) == 'bestmatch'


def test_user_selected_sort(service, identity_simple, records):
    """Chosen sort method."""
    res = service.search(
        identity_simple, q='test', sort='mostrecent', page=1, size=10,
        _max_results=100).to_dict()
    assert sort_method(res) == 'mostrecent'


def test_invalid_sort(service, identity_simple, records):
    """Test invalid sort key."""
    # Search with non existing sort parameter
    pytest.raises(ValidationError, service.search, identity_simple, sort="foo")


def test_mostrecent(service, identity_simple, records):
    """Chosen sort method."""
    res = service.search(
        identity_simple, sort='mostrecent', page=1, size=10,
        _max_results=100).to_dict()
    assert sort_method(res) == 'mostrecent'
    assert order(res) == [2, 1, 0]
