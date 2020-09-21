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
from invenio_pidstore.errors import PIDDeletedError
from invenio_search import current_search, current_search_client
from marshmallow import ValidationError


@pytest.fixture()
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        'metadata': {
            'title': 'Test'
        },
    }


def test_simple_flow(app, service, identity_simple, input_data):
    """Create a record."""
    idx = 'records-record-v1.0.0'

    # Create an item
    item = service.create(identity_simple, input_data)
    id_ = item.id

    # Read it
    read_item = service.read(id_, identity_simple)
    assert item.id == read_item.id
    assert item.data == read_item.data

    # TODO: Should this be part of the service? we don't know the index easily
    current_search.flush_and_refresh(idx)

    # Search it
    res = service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 1
    assert list(res.hits)[0] == read_item.data

    # Update it
    data = read_item.data
    data['metadata']['title'] = 'New title'
    update_item = service.update(id_, identity_simple, data)
    assert item.id == update_item.id
    assert update_item['metadata']['title'] == 'New title'

    # Delete it
    assert service.delete(id_, identity_simple)
    current_search.flush_and_refresh(idx)

    # Retrieve it - deleted so cannot
    # - db
    pytest.raises(PIDDeletedError, service.read, id_, identity_simple)
    # - search
    res = service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 0


def test_sorting_in_search(app, service, identity_simple, input_data):
    """Search a record."""
    idx = 'records-record-v1.0.0'

    # Create an item
    first_item = service.create(identity_simple, input_data)

    input_data["metadata"]["title"] = "Another Test"
    second_item = service.create(identity_simple, input_data)

    # TODO: Should this be part of the service? we don't know the index easily
    current_search.flush_and_refresh(idx)

    # Search no query and no sort should sort by the most recent created record
    res = service.search(identity_simple)

    assert res.total == 2
    assert list(res.hits)[0] == second_item.data

    # Search with query and no sort should sort by the bestmatch record
    res = service.search(identity_simple, q="title:Test")

    assert res.total == 2
    assert list(res.hits)[0] == first_item.data

    # Search with existing sort parameter
    res = service.search(identity_simple, sort="mostrecent")

    assert res.total == 2
    assert list(res.hits)[0] == second_item.data

    # Search with non existing sort parameter
    pytest.raises(ValidationError, service.search, identity_simple, sort="foo")
