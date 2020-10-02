# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test faceting."""

import time
from copy import deepcopy

import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_search import current_search
from mock_module.api import Record
from mock_module.service import Service

# 2 things to test
# 1- results are aggregated / post_filtered
# 2- links are generated


@pytest.fixture(scope="module")
def three_indexed_records(app, identity_simple, es):
    # NOTE: es is used (and not es_clear) here because all tests
    #       assume 3 records have been indexed and NO tests in this module
    #       adds/deletes any.
    service = Service()

    def _create(metadata):
        data = {
            'metadata': {
                'title': 'Test',
                **metadata
            },
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
        "type": {
            "buckets": [
                {
                    "doc_count": 2,
                    "key": "A",
                    "subtype": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "key": "AA"
                            },
                            {
                                "doc_count": 1,
                                "key": "AB"
                            }
                        ],
                        'doc_count_error_upper_bound': 0,
                        'sum_other_doc_count': 0
                    }
                },
                {
                    "doc_count": 1,
                    "key": "B",
                    "subtype": {
                        "buckets": [],
                        'doc_count_error_upper_bound': 0,
                        'sum_other_doc_count': 0
                    }
                }
            ],
            'doc_count_error_upper_bound': 0,
            'sum_other_doc_count': 0,
        }
    }
    assert expected_aggs == response_aggs


def test_post_filtering(client, headers, three_indexed_records):
    response = client.get("/mocks?type=A", headers=headers)

    assert response.status_code == 200

    # Test aggregation is the same
    response_aggs = response.json["aggregations"]
    expected_aggs = {
        "type": {
            "buckets": [
                {
                    "doc_count": 2,
                    "key": "A",
                    "subtype": {
                        "buckets": [
                            {
                                "doc_count": 1,
                                "key": "AA"
                            },
                            {
                                "doc_count": 1,
                                "key": "AB"
                            }
                        ],
                        'doc_count_error_upper_bound': 0,
                        'sum_other_doc_count': 0
                    }
                },
                {
                    "doc_count": 1,
                    "key": "B",
                    "subtype": {
                        "buckets": [],
                        'doc_count_error_upper_bound': 0,
                        'sum_other_doc_count': 0
                    }
                }
            ],
            'doc_count_error_upper_bound': 0,
            'sum_other_doc_count': 0,
        }
    }
    assert expected_aggs == response_aggs

    # Test hits are filtered
    response_hits = response.json["hits"]["hits"]
    assert 2 == len(response_hits)
    assert set(["Record 1", "Record 2"]) == set(
        [h["metadata"]["title"] for h in response_hits]
    )


#
# 2- links are generated
#
def test_links_keep_facets(client, headers, three_indexed_records):
    response = client.get("/mocks?type=A&subtype=B", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": (
            "https://localhost:5000/api/mocks?"
            "page=1&size=25&sort=newest&subtype=B&type=A"
        ),
    }
    for key, url in expected_links.items():
        assert url == response_links[key]


def test_links_keep_repeated_facets(client, headers, three_indexed_records):
    response = client.get(
        "/mocks?size=1&type=B&type=A",
        headers=headers
    )

    response_links = response.json["links"]
    expected_links = {
        "self": (
            "https://localhost:5000/api/mocks?page=1&size=1&sort=newest"
            "&type=B&type=A"
        ),
        "next": (
            "https://localhost:5000/api/mocks?page=2&size=1&sort=newest"
            "&type=B&type=A"
        ),
    }
    for key, url in expected_links.items():
        assert url == response_links[key]
