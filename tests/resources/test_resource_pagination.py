# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test pagination."""

import pytest

from invenio_records_resources.services import RecordService
from tests.mock_module.api import Record
from tests.mock_module.config import ServiceConfig

# 2 things to test
# 1- results are paginated
# 2- links are generated


@pytest.fixture(scope="module")
def three_indexed_records(app, identity_simple, search):
    # NOTE: We make use of search fixture (and not search_clear) here because all tests
    #       assume 3 records have been indexed and NO tests in this module
    #       adds/deletes any.
    service = RecordService(ServiceConfig)

    for i in range(3):
        data = {
            "metadata": {
                "title": f"Test foo {i}",
            },
        }
        service.create(identity_simple, data)

    Record.index.refresh()


@pytest.fixture(scope="module")
def search_options(app, service):
    return service.config.search.pagination_options


#
# 1- results are paginated
#


def assert_hits_len(response, expected_hits):
    """Assert number of hits."""
    assert 200 == response.status_code
    assert expected_hits == len(response.json["hits"]["hits"])


def test_pagination_defaults(client, headers, three_indexed_records):
    # Test that default querystring pagination values are used if none
    # specified. Those should allow for 3 records to show up in response.
    response = client.get("/mocks", headers=headers)

    assert_hits_len(response, 3)


def test_pagination_page(client, headers, search_options, three_indexed_records):
    response = client.get("/mocks?page=1", headers=headers)
    assert_hits_len(response, 3)

    response = client.get("/mocks?page=2", headers=headers)
    assert_hits_len(response, 0)

    default_max_results = search_options["default_max_results"]
    default_size = search_options["default_results_per_page"]
    invalid_page = default_max_results // default_size + 1

    response = client.get(f"/mocks?page={invalid_page}", headers=headers)
    assert response.status_code == 400


def test_pagination_size(client, headers, search_options, three_indexed_records):
    response = client.get("/mocks?size=10", headers=headers)
    assert_hits_len(response, 3)

    response = client.get("/mocks?size=1", headers=headers)
    assert_hits_len(response, 1)

    response = client.get("/mocks?size=0", headers=headers)
    assert response.status_code == 400

    # NOTE: There are no invalid sizes. Size is always capped by max results


def test_pagination_page_and_size(client, headers, three_indexed_records):
    response = client.get("/mocks?size=10&page=1", headers=headers)
    assert_hits_len(response, 3)

    response = client.get("/mocks?page=2&size=1", headers=headers)
    assert_hits_len(response, 1)

    response = client.get("/mocks?page=20size=1000", headers=headers)
    assert response.status_code == 400


#
# 2- links are generated
#
def test_middle_search_result_has_next_and_prev_links(
    client, headers, three_indexed_records
):
    response = client.get("/mocks?size=1&page=2", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": "https://127.0.0.1:5000/api/mocks?page=2&size=1&sort=newest",
        "prev": "https://127.0.0.1:5000/api/mocks?page=1&size=1&sort=newest",
        "next": "https://127.0.0.1:5000/api/mocks?page=3&size=1&sort=newest",
    }

    # NOTE: This is done so that we only test for pagination links
    for key, url in expected_links.items():
        assert key in response_links
        assert url == response_links[key]


def test_first_search_result_has_next_and_no_prev_link(
    client, headers, three_indexed_records
):
    response = client.get("/mocks?size=1&page=1", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": "https://127.0.0.1:5000/api/mocks?page=1&size=1&sort=newest",
        "next": "https://127.0.0.1:5000/api/mocks?page=2&size=1&sort=newest",
    }
    for key, url in expected_links.items():
        assert url == response_links[key]

    assert "prev" not in response_links


def test_last_search_result_has_prev_link_and_no_next_link(
    client, headers, three_indexed_records
):
    response = client.get("/mocks?size=1&page=3", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": "https://127.0.0.1:5000/api/mocks?page=3&size=1&sort=newest",
        "prev": "https://127.0.0.1:5000/api/mocks?page=2&size=1&sort=newest",
    }
    for key, url in expected_links.items():
        assert url == response_links[key]

    assert "next" not in response_links


def test_beyond_last_search_has_prev_link_and_no_next_link(
    client, headers, search_options, three_indexed_records
):
    response = client.get("/mocks?size=1&page=4", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": "https://127.0.0.1:5000/api/mocks?page=4&size=1&sort=newest",
        "prev": "https://127.0.0.1:5000/api/mocks?page=3&size=1&sort=newest",
    }
    for key, url in expected_links.items():
        assert url == response_links[key]

    assert "next" not in response_links


def test_beyond_beyond_last_search_has_no_prev_or_next_link(
    client, headers, search_options, three_indexed_records
):
    response = client.get("/mocks?size=1&page=5", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": "https://127.0.0.1:5000/api/mocks?page=5&size=1&sort=newest",
    }
    for key, url in expected_links.items():
        assert url == response_links[key]

    assert "prev" not in response_links
    assert "next" not in response_links


def test_searchstring_is_preserved(client, headers, three_indexed_records):
    response = client.get("/mocks?size=1&page=2&q=test+foo", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": (
            "https://127.0.0.1:5000/api/mocks?page=2&q=test+foo&size=1"
            "&sort=bestmatch"
        ),
        "prev": (
            "https://127.0.0.1:5000/api/mocks?page=1&q=test+foo&size=1"
            "&sort=bestmatch"
        ),
        "next": (
            "https://127.0.0.1:5000/api/mocks?page=3&q=test+foo&size=1"
            "&sort=bestmatch"
        ),
    }
    for key, url in expected_links.items():
        assert url == response_links[key]
