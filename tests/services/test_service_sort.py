# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Sort tests."""

import time

import pytest
from marshmallow import ValidationError
from mock_module.api import Record


#
# Helpers
#
def ids(res):
    """Returns ids of the result list."""
    return [h["id"] for h in res]


#
# Fixtures
#
@pytest.fixture(scope="module")
def records(app, service, identity_simple):
    """Input data (as coming from the view layer)."""
    parts = ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]
    length = len(parts)
    results = []
    for i in range(3):
        data = {
            "metadata": {"title": " ".join(parts[: length - 3 * i])},
        }
        time.sleep(0.01)
        results += [service.create(identity_simple, data).to_dict()]

    Record.index.refresh()

    return results


#
# Tests
#
def test_default_no_query(service, identity_simple, records):
    """Default sorting without a query."""
    res = service.search(identity_simple, page=1, size=10, _max_results=100).to_dict()
    # default no query is to order by newest (last created first)
    assert ids(reversed(records)) == ids(res["hits"]["hits"])


def test_user_selected_sort(service, identity_simple, records):
    """Chosen sort method."""
    res = service.search(
        identity_simple, sort="newest", page=1, size=10, _max_results=100
    ).to_dict()
    assert ids(reversed(records)) == ids(res["hits"]["hits"])


def test_invalid_sort(service, identity_simple, records):
    """Test invalid sort key."""
    # Search with non existing sort parameter
    pytest.raises(ValidationError, service.search, identity_simple, sort="foo")
