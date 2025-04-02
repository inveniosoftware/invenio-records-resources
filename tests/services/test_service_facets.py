# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020-2023 Northwestern University.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets tests."""

import pytest

from tests.mock_module.api import Record


#
# Fixtures
#
@pytest.fixture()
def records(app, service, identity_simple, search_clear):
    """Input data (as coming from the view layer)."""
    items = []
    for idx in range(2):
        data = {
            "metadata": {
                "title": f"00{idx}",
                "type": {"type": f"Foo{idx}", "subtype": f"Bar{idx}"},
            },
        }
        items.append(service.create(identity_simple, data))
    Record.index.refresh()
    return items


#
# Tests
#
def test_facets(app, service, identity_simple, records):
    # Search it
    res = service.search(identity_simple)
    service_aggs = res.aggregations

    expected_aggs = {
        "subjects": {
            "buckets": [],
            "label": "Subjects",
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
        "subjects": {
            "buckets": [],
            "label": "Subjects",
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
        identity_simple, facets={"type": ["Foo1"], "subjects": ["Subject0"]}
    )
    service_aggs = res.aggregations
    expected_aggs = {
        "subjects": {
            "buckets": [],
            "label": "Subjects",
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
        "subjects": {
            "buckets": [],
            "label": "Subjects",
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


def test_combined_terms_facets(app, service, identity_simple, search_clear):
    # Create records with nested patterns of interest
    data = {
        "metadata": {
            "title": "SU1 + (SC1, SU2)",
            "subjects": [
                {"subject": "SU1"},  # should be ignored in aggregation results
                {"scheme": "SC1", "subject": "SU2"},
            ],
            # Note that you would typically want to have a mechanism in place to
            # auto-fill this field based on the values in "subjects"
            "combined_subjects": [
                "SU1",  # should be ignored in aggregation results
                "SC1::SU2",
            ],
        },
    }
    service.create(identity_simple, data)
    data = {
        "metadata": {
            "title": "(SC1, SU2) + (SC2, SU3)",
            "subjects": [
                {"scheme": "SC1", "subject": "SU2"},
                {"scheme": "SC2", "subject": "SU3"},
            ],
            "combined_subjects": ["SC1::SU2", "SC2::SU3"],
        },
    }
    service.create(identity_simple, data)
    data = {
        "metadata": {
            "title": "(SC1, SU3)",
            "subjects": [
                {"scheme": "SC1", "subject": "SU3"},
            ],
            "combined_subjects": ["SC1::SU3"],
        },
    }
    service.create(identity_simple, data)
    Record.index.refresh()

    # Action
    res = service.search(identity_simple)
    service_aggs = res.aggregations

    expected_aggs = {
        "subjects": {
            "buckets": [
                {
                    "doc_count": 3,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 2,
                                "is_selected": False,
                                "key": "SU2",
                                "label": "SU2",
                            },
                            {
                                "doc_count": 1,
                                "is_selected": False,
                                "key": "SU3",
                                "label": "SU3",
                            },
                        ]
                    },
                    "is_selected": False,
                    "key": "SC1",
                    "label": "SC1",
                },
                {
                    "doc_count": 1,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "is_selected": False,
                                "key": "SU3",
                                "label": "SU3",
                            },
                        ]
                    },
                    "is_selected": False,
                    "key": "SC2",
                    "label": "SC2",
                },
            ],
            "label": "Subjects",
        },
        "type": {
            "buckets": [],
            "label": "Type",
        },
    }
    assert expected_aggs == service_aggs
