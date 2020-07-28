# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test pagination."""

import json
from copy import deepcopy

import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_search import current_search

from invenio_records_resources.schemas.url_args import DEFAULT_MAX_RESULTS, \
    DEFAULT_RESULTS_PER_PAGE
from invenio_records_resources.services import RecordService

HEADERS = {"content-type": "application/json", "accept": "application/json"}

# 2 things to test
# 1- results are paginated
# 2- links are generated


@pytest.fixture("module")
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method='system_role', value='any_user'))
    return i


@pytest.fixture("module")
def three_indexed_records(app, input_service_data, identity_simple, es):
    # NOTE: We make use of es fixture (and not es_clear) here because all tests
    #       assume 3 records have been indexed and NO tests in this module
    #       adds/deletes any.
    record_service = RecordService()
    search_class = record_service.config.search_cls
    for i in range(3):
        data = deepcopy(input_service_data)
        data["title"] += f" {i}"
        record_service.create(data, identity_simple)
        current_search.flush_and_refresh(search_class.Meta.index)


#
# 1- results are paginated
#


def assert_hits_len(response, expected_hits):
    """Assert number of hits."""
    assert response.status_code == 200
    assert len(response.json['hits']['hits']) == expected_hits


def test_pagination_defaults(client, three_indexed_records):
    # Test that default querystring pagination values are used if none
    # specified. Those should allow for 3 records to show up in response.
    response = client.get("/records", headers=HEADERS)

    assert_hits_len(response, 3)


def test_pagination_page(client, three_indexed_records):
    response = client.get("/records?page=1", headers=HEADERS)
    assert_hits_len(response, 3)

    response = client.get("/records?page=2", headers=HEADERS)
    assert_hits_len(response, 0)

    invalid_page = DEFAULT_MAX_RESULTS // DEFAULT_RESULTS_PER_PAGE + 1
    response = client.get(
        "/records?page={}".format(invalid_page),
        headers=HEADERS
    )
    assert response.status_code == 400


def test_pagination_size(client, three_indexed_records):
    response = client.get("/records?size=10", headers=HEADERS)
    assert_hits_len(response, 3)

    response = client.get("/records?size=1", headers=HEADERS)
    assert_hits_len(response, 1)

    response = client.get("/records?size=0", headers=HEADERS)
    assert response.status_code == 400

    invalid_size = DEFAULT_MAX_RESULTS + 1
    response = client.get(
        "/records?size={}".format(invalid_size),
        headers=HEADERS
    )
    assert response.status_code == 400


def test_pagination_page_and_size(client, three_indexed_records):
    response = client.get("/records?size=10&page=1", headers=HEADERS)
    assert_hits_len(response, 3)

    response = client.get("/records?page=2&size=1", headers=HEADERS)
    assert_hits_len(response, 1)

    response = client.get("/records?page=20size=1000", headers=HEADERS)
    assert response.status_code == 400


#
# 2- links are generated
#

def test_middle_search_result_has_next_and_prev_links(
        client, three_indexed_records):
    response = client.get("/records?size=1&page=2", headers=HEADERS)

    response_links = response.json["links"]
    expected_links = {
        "self": "https://localhost:5000/api/records?size=1&page=2",
        "prev": "https://localhost:5000/api/records?size=1&page=1",
        "next": "https://localhost:5000/api/records?size=1&page=3",
    }
    # NOTE: This is done so that we only test for pagination links
    for key, url in expected_links.items():
        assert url == response_links[key]


def test_first_search_result_has_next_and_no_prev_link(
        client, three_indexed_records):
    response = client.get("/records?size=1&page=1", headers=HEADERS)

    response_links = response.json["links"]
    expected_links = {
        "self": "https://localhost:5000/api/records?size=1&page=1",
        "next": "https://localhost:5000/api/records?size=1&page=2",
    }
    # NOTE: This is done so that we only test for pagination links
    for key, url in expected_links.items():
        assert url == response_links[key]

    assert "prev" not in response_links


def test_last_search_result_has_next_and_prev_links(
        client, three_indexed_records):
    # NOTE: We are replicating invenio-records-rest approach which could be
    #       discussed.
    response = client.get("/records?size=1&page=3", headers=HEADERS)

    response_links = response.json["links"]
    expected_links = {
        "self": "https://localhost:5000/api/records?size=1&page=3",
        "prev": "https://localhost:5000/api/records?size=1&page=2",
        "next": "https://localhost:5000/api/records?size=1&page=4",
    }
    # NOTE: This is done so that we only test for pagination links
    for key, url in expected_links.items():
        assert url == response_links[key]


def test_max_search_result_has_prev_and_no_next_link(
        client, three_indexed_records):
    # NOTE: We are replicating invenio-records-rest approach which could be
    #       discussed.
    max_results = DEFAULT_MAX_RESULTS

    response = client.get(
        f"/records?size=1&page={max_results}",
        headers=HEADERS
    )

    response_links = response.json["links"]
    expected_links = {
        "self": (
            f"https://localhost:5000/api/records?size=1&page={max_results}"
        ),
        "prev": (
            f"https://localhost:5000/api/records?size=1&page={max_results - 1}"
        ),
    }
    # NOTE: This is done so that we only test for pagination links
    for key, url in expected_links.items():
        assert url == response_links[key]

    assert "next" not in response_links


def test_searchstring_is_preserved(client, three_indexed_records):
    response = client.get(
        "/records?size=1&page=2&q=Romans+story",
        headers=HEADERS
    )

    response_links = response.json["links"]
    expected_links = {
        "self": (
            "https://localhost:5000/api/records?size=1&page=2&q=Romans+story"
        ),
        "prev": (
            "https://localhost:5000/api/records?size=1&page=1&q=Romans+story"
        ),
        "next": (
            "https://localhost:5000/api/records?size=1&page=3&q=Romans+story"
        ),
    }
    # NOTE: This is done so that we only test for pagination links
    for key, url in expected_links.items():
        assert url == response_links[key]
