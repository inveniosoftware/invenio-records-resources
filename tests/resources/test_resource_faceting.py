# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020-2023 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test faceting."""


import pytest

from invenio_records_resources.services import RecordService
from tests.mock_module.api import Record
from tests.mock_module.config import ServiceConfig

# 2 things to test
# 1- results are aggregated / post_filtered
# 2- links are generated


@pytest.fixture()
def three_indexed_records(app, identity_simple, search_clear):
    # NOTE: search is used (and not search_clear) here because all tests
    #       assume 3 records have been indexed and NO tests in this module
    #       adds/deletes any.
    service = RecordService(ServiceConfig)

    def _create(metadata):
        data = {
            "metadata": {"title": "Test", **metadata},
        }
        service.create(identity_simple, data)

    _create({"title": "Record 1", "type": {"type": "A", "subtype": "AA"}})
    _create({"title": "Record 2", "type": {"type": "A", "subtype": "AB"}})
    _create({"title": "Record 3", "type": {"type": "B"}})

    Record.index.refresh()


#
# 1- results are aggregated / post_filtered
#


def test_aggregating(client, headers, three_indexed_records):
    response = client.get("/mocks", headers=headers)
    response_aggs = response.json["aggregations"]

    expected_aggs = {
        "subjects": {
            "buckets": [],
            "label": "Subjects",
        },
        "type": {
            "label": "Type",
            "buckets": [
                {
                    "doc_count": 2,
                    "key": "A",
                    "label": "A",
                    "is_selected": False,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "key": "AA",
                                "label": "AA",
                                "is_selected": False,
                            },
                            {
                                "doc_count": 1,
                                "key": "AB",
                                "label": "AB",
                                "is_selected": False,
                            },
                        ],
                    },
                },
                {
                    "doc_count": 1,
                    "key": "B",
                    "label": "B",
                    "is_selected": False,
                    "inner": {"buckets": []},
                },
            ],
        },
    }
    assert expected_aggs == response_aggs


def test_post_filtering(client, headers, three_indexed_records):
    response = client.get("/mocks?type=A", headers=headers)

    assert response.status_code == 200

    # Test aggregation is the same
    response_aggs = response.json["aggregations"]
    expected_aggs = {
        "subjects": {
            "buckets": [],
            "label": "Subjects",
        },
        "type": {
            "label": "Type",
            "buckets": [
                {
                    "doc_count": 2,
                    "key": "A",
                    "label": "A",
                    "is_selected": True,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "key": "AA",
                                "label": "AA",
                                "is_selected": False,
                            },
                            {
                                "doc_count": 1,
                                "key": "AB",
                                "label": "AB",
                                "is_selected": False,
                            },
                        ],
                    },
                },
                {
                    "doc_count": 1,
                    "key": "B",
                    "label": "B",
                    "is_selected": False,
                    "inner": {"buckets": []},
                },
            ],
        },
    }
    assert expected_aggs == response_aggs

    # Test hits are filtered
    response_hits = response.json["hits"]["hits"]
    assert 2 == len(response_hits)
    assert set(["Record 1", "Record 2"]) == set(
        [h["metadata"]["title"] for h in response_hits]
    )


def test_nested_post_filtering(client, headers, identity_simple, service, search_clear):
    data = {
        "metadata": {
            "title": "SU1 + (SC1, SU2)",
            "subjects": [
                {"subject": "SU1"},  # should be ignored in aggregation results
                {"scheme": "SC1", "subject": "SU2"},
            ],
            "combined_subjects": ["SC1::SU2"],
        },
    }
    service.create(identity_simple, data)
    data = {
        "metadata": {
            "title": "(SC1, SU4) + (SC2, SU2)",
            "subjects": [
                {"scheme": "SC1", "subject": "SU4"},
                {"scheme": "SC2", "subject": "SU2"},
            ],
            "combined_subjects": ["SC1::SU4", "SC2::SU2"],
        },
    }
    service.create(identity_simple, data)
    data = {
        "metadata": {
            "title": "(SC2, SU3)",
            "subjects": [
                {"scheme": "SC2", "subject": "SU3"},
            ],
            "combined_subjects": ["SC2::SU3"],
        },
    }
    service.create(identity_simple, data)
    Record.index.refresh()

    # First scenario
    # Test that:
    # - different subjects/subfields but same scheme result in a union post_filter
    #   (a record that only has 1 of the scheme+subject should be selected)
    # - hierarchical dependency is enforced (selects for scheme AND subject together)
    response = client.get("/mocks?subjects=SC1::SU2&subjects=SC1::SU3", headers=headers)
    resource_aggs = response.json["aggregations"]

    expected_aggs = {
        "subjects": {
            "buckets": [
                {
                    "doc_count": 2,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "is_selected": True,
                                "key": "SU2",
                                "label": "SU2",
                            },
                            {
                                "doc_count": 1,
                                "is_selected": False,
                                "key": "SU4",
                                "label": "SU4",
                            },
                        ]
                    },
                    "is_selected": False,  # only selected if SC1 is separately passed
                    "key": "SC1",
                    "label": "SC1",
                },
                {
                    "doc_count": 2,
                    "inner": {
                        "buckets": [
                            {
                                "doc_count": 1,
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
    assert expected_aggs == resource_aggs
    hits = response.json["hits"]["hits"]
    assert 1 == len(hits)
    assert "SU1 + (SC1, SU2)" == hits[0]["metadata"]["title"]

    # 2nd scenario
    # Test that:
    # - different schemes/fields result in a union post_filter as well
    #   (a record that only has 1 of the scheme+subject should be selected)
    response = client.get("/mocks?subjects=SC1::SU1&subjects=SC2::SU3", headers=headers)
    resource_aggs = response.json["aggregations"]

    # Reformat expected_aggs
    inner = expected_aggs["subjects"]["buckets"][0]["inner"]
    inner["buckets"][0]["is_selected"] = False
    expected_aggs["subjects"]["buckets"][1]["inner"]["buckets"][1]["is_selected"] = True
    assert expected_aggs == resource_aggs
    hits = response.json["hits"]["hits"]
    assert 1 == len(hits)
    assert "(SC2, SU3)" == hits[0]["metadata"]["title"]


#
# 2- links are generated
#
def test_links_keep_facets(client, headers, three_indexed_records):
    response = client.get("/mocks?type=A**B", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": (
            "https://127.0.0.1:5000/api/mocks?page=1&size=25&sort=newest&type=A**B"
        ),
    }
    for key, url in expected_links.items():
        assert url == response_links[key]


def test_links_keep_repeated_facets(client, headers, three_indexed_records):
    response = client.get("/mocks?size=1&type=B&type=A", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": (
            "https://127.0.0.1:5000/api/mocks?page=1&size=1&sort=newest"
            "&type=B&type=A"
        ),
        "next": (
            "https://127.0.0.1:5000/api/mocks?page=2&size=1&sort=newest"
            "&type=B&type=A"
        ),
    }
    for key, url in expected_links.items():
        assert url == response_links[key]
