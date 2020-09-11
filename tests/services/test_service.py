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
    read_item = service.read(identity_simple, id_)
    assert item.id == read_item.id
    assert item.record == read_item.record
    assert item.pids == read_item.pids

    # TODO: Should this be part of the service? we don't know the index easily
    current_search.flush_and_refresh(idx)

    # Search it
    res = service.search(identity_simple, f"id:{id_}")
    assert res.total == 1
    assert res.records[0].record == read_item.record

    # Update it
    data = read_item.record
    data['metadata']['title'] = 'New title'
    update_item = service.update(identity_simple, id_, data)
    assert item.id == update_item.id
    assert update_item.record['metadata']['title'] == 'New title'
    assert item.pids == update_item.pids

    # Delete it
    assert service.delete(identity_simple, id_)
    current_search.flush_and_refresh(idx)

    # Retrieve it - deleted so cannot
    # - db
    pytest.raises(PIDDeletedError, service.read, identity_simple, id_)
    # - search
    res = service.search(identity_simple, f"id:{id_}")
    assert res.total == 0
