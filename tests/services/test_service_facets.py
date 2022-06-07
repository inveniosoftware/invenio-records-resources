# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets tests."""

import pytest
from mock_module.api import Record


#
# Fixtures
#
@pytest.fixture(scope="module")
def records(app, service, identity_simple):
    """Input data (as coming from the view layer)."""
    items = []
    for idx in range(2):
        data = {
            "metadata": {
                "title": f"00{idx}",
                "type": {"type": f"Foo{idx}", "subtype": f"Bar{idx}"},
                "subject": f"Subject{idx}",
            },
        }
        items.append(service.create(identity_simple, data))
    Record.index.refresh()
    return items


#
# Tests
#
def test_facets(app, service, identity_simple, records):
    """Create a record."""
    # Search it
    res = service.search(identity_simple)
    service_aggs = res.aggregations

    expected_aggs = {
        "subject": {
            "buckets": [
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "Subject0",
                    "label": "Subject0",
                },
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "Subject1",
                    "label": "Subject1",
                },
            ],
            "label": "Subject",
        },
        "type": {
            "buckets": [
                {
                    "doc_count": 1,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "is_selected": False,
                                "key": "Bar0",
                                "label": "Bar0",
                            }
                        ]
                    },
                    "is_selected": False,
                    "key": "Foo0",
                    "label": "Foo0",
                },
                {
                    "doc_count": 1,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "is_selected": False,
                                "key": "Bar1",
                                "label": "Bar1",
                            }
                        ]
                    },
                    "is_selected": False,
                    "key": "Foo1",
                    "label": "Foo1",
                },
            ],
            "label": "Type",
        },
    }

    assert expected_aggs == service_aggs


def test_facets_post_filtering_union(app, service, identity_simple, records):
    """Same facets should result in union of results."""
    # Search it
    res = service.search(identity_simple, facets={"type": ["Foo0", "Foo1"]})
    service_aggs = res.aggregations
    expected_aggs = {
        "subject": {
            "buckets": [
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "Subject0",
                    "label": "Subject0",
                },
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "Subject1",
                    "label": "Subject1",
                },
            ],
            "label": "Subject",
        },
        "type": {
            "label": "Type",
            "buckets": [
                {
                    "doc_count": 1,
                    "key": "Foo0",
                    "label": "Foo0",
                    "is_selected": True,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "key": "Bar0",
                                "label": "Bar0",
                                "is_selected": False,
                            },
                        ],
                    },
                },
                {
                    "doc_count": 1,
                    "key": "Foo1",
                    "label": "Foo1",
                    "is_selected": True,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "key": "Bar1",
                                "label": "Bar1",
                                "is_selected": False,
                            },
                        ],
                    },
                },
            ],
        },
    }
    assert expected_aggs == service_aggs
    # Test hits contain items from both
    assert 2 == len(res)
    assert set(["000", "001"]) == set([h["metadata"]["title"] for h in res])


def test_facets_post_filtering_intersection(app, service, identity_simple, records):
    """Different facets should result in intersection of results."""
    # No records match both facets
    res = service.search(
        identity_simple, facets={"type": ["Foo1"], "subject": ["Subject0"]}
    )
    service_aggs = res.aggregations
    expected_aggs = {
        "subject": {
            "buckets": [
                {
                    "doc_count": 1,
                    "is_selected": True,
                    "key": "Subject0",
                    "label": "Subject0",
                },
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "Subject1",
                    "label": "Subject1",
                },
            ],
            "label": "Subject",
        },
        "type": {
            "label": "Type",
            "buckets": [
                {
                    "doc_count": 1,
                    "key": "Foo0",
                    "label": "Foo0",
                    "is_selected": False,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "key": "Bar0",
                                "label": "Bar0",
                                "is_selected": False,
                            },
                        ],
                    },
                },
                {
                    "doc_count": 1,
                    "key": "Foo1",
                    "label": "Foo1",
                    "is_selected": True,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "key": "Bar1",
                                "label": "Bar1",
                                "is_selected": False,
                            },
                        ],
                    },
                },
            ],
        },
    }
    assert expected_aggs == service_aggs
    # Test hits are filtered
    assert 0 == len(res)


def test_facets_post_filtering(app, service, identity_simple, records):
    """Create a record."""
    # Search it
    res = service.search(identity_simple, facets={"type": ["Foo1"]})
    service_aggs = res.aggregations
    expected_aggs = {
        "subject": {
            "buckets": [
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "Subject0",
                    "label": "Subject0",
                },
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "Subject1",
                    "label": "Subject1",
                },
            ],
            "label": "Subject",
        },
        "type": {
            "label": "Type",
            "buckets": [
                {
                    "doc_count": 1,
                    "key": "Foo0",
                    "label": "Foo0",
                    "is_selected": False,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "key": "Bar0",
                                "label": "Bar0",
                                "is_selected": False,
                            },
                        ],
                    },
                },
                {
                    "doc_count": 1,
                    "key": "Foo1",
                    "label": "Foo1",
                    "is_selected": True,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "key": "Bar1",
                                "label": "Bar1",
                                "is_selected": False,
                            },
                        ],
                    },
                },
            ],
        },
    }
    assert expected_aggs == service_aggs
    # Test hits are filtered
    assert 1 == len(res)
    assert set(["001"]) == set([h["metadata"]["title"] for h in res])
