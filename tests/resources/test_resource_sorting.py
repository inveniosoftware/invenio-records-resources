# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test sorting."""

import time
from copy import deepcopy

import pytest
from mock_module.api import Record
from mock_module.config import ServiceConfig

from invenio_records_resources.services import RecordService

# 3 things to test
# 0- search options are configurable (see mock_module)
# 1- results are sorted
# 2- links are generated


@pytest.fixture(scope="module")
def three_indexed_records(app, identity_simple, search):
    # NOTE: We make use of search fixture (and not search_clear) here because all tests
    #       assume 3 records have been indexed and NO tests in this module
    #       adds/deletes any.
    input_data = {
        "metadata": {"title": "Test"},
    }
    service = RecordService(ServiceConfig)
    title_parts = [
        "The",
        "quick",
        "brown",
        "fox",
        "jumps",
        "over",
        "the",
        "lazy",
        "dog",
    ]
    title_parts_len = len(title_parts)

    units = []
    for i in range(3):
        data = deepcopy(input_data)
        data["metadata"]["title"] = " ".join(title_parts[: title_parts_len - 3 * i])
        time.sleep(0.01)
        units += [service.create(identity_simple, data)]

    Record.index.refresh()

    return units


#
# 1- results are sorted
#


def test_default_sorting_if_no_query(client, headers, three_indexed_records):
    # NOTE: the default sorting in this case is by most recently created
    response = client.get("/mocks", headers=headers)

    for i, hit in enumerate(response.json["hits"]["hits"]):
        assert three_indexed_records[2 - i].id == hit["id"]


def test_default_sorting_if_query(client, headers, three_indexed_records):
    response = client.get("/mocks?q=over+the+lazy+dog", headers=headers)

    for i, hit in enumerate(response.json["hits"]["hits"]):
        assert three_indexed_records[i].id == hit["id"]


def test_explicit_sort(client, headers, three_indexed_records):
    response = client.get("/mocks?sort=newest", headers=headers)

    for i, hit in enumerate(response.json["hits"]["hits"]):
        assert three_indexed_records[2 - i].id == hit["id"]


def test_explicit_sort_reversed(client, headers, three_indexed_records):
    response = client.get("/mocks?sort=oldest", headers=headers)

    for i, hit in enumerate(response.json["hits"]["hits"]):
        assert three_indexed_records[i].id == hit["id"]


#
# 3- links are generated
#


def test_sort_in_links_no_matter_if_sort_in_url(client, headers, three_indexed_records):
    response = client.get("/mocks?size=1&sort=newest", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": ("https://127.0.0.1:5000/api/mocks?page=1&size=1&sort=newest"),
        "next": ("https://127.0.0.1:5000/api/mocks?page=2&size=1&sort=newest"),
    }
    # NOTE: This is done so that we only test for pagination links
    for key, url in expected_links.items():
        assert url == response_links[key]

    response = client.get("/mocks?size=1", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": ("https://127.0.0.1:5000/api/mocks?page=1&size=1&sort=newest"),
        "next": ("https://127.0.0.1:5000/api/mocks?page=2&size=1&sort=newest"),
    }
    for key, url in expected_links.items():
        assert url == response_links[key]


def test_searchstring_is_preserved(client, headers, three_indexed_records):
    response = client.get("/mocks?q=the+quick&sort=newest", headers=headers)

    response_links = response.json["links"]
    expected_links = {
        "self": (
            "https://127.0.0.1:5000/api/mocks?page=1&q=the%20quick&size=25"
            "&sort=newest"
        ),
    }
    for key, url in expected_links.items():
        assert url == response_links[key]
