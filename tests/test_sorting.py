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
from flask_principal import Identity, Need, UserNeed
from invenio_search import current_search

from invenio_records_resources.services import RecordService

HEADERS = {"content-type": "application/json", "accept": "application/json"}

# 2 things to test
# 1- results are sorted
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
    title_parts = [
        "The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"
    ]
    title_parts_len = len(title_parts)
    units = []
    for i in range(3):
        data = deepcopy(input_service_data)
        data["title"] = " ".join(title_parts[:title_parts_len-3*i])
        time.sleep(0.01)
        units += [record_service.create(identity_simple, data)]

    current_search.flush_and_refresh(search_class.Meta.index)

    return units


#
# 1- results are sorted
#


def test_default_sorting_if_no_query(client, three_indexed_records):
    # NOTE: the default sorting in this case is by most recently created
    response = client.get("/records", headers=HEADERS)

    for i, hit in enumerate(response.json['hits']['hits']):
        assert three_indexed_records[2-i].id == hit["pid"]


def test_default_sorting_if_query(client, three_indexed_records):
    response = client.get("/records?q=over+the+lazy+dog", headers=HEADERS)

    for i, hit in enumerate(response.json['hits']['hits']):
        assert three_indexed_records[i].id == hit["pid"]


# def test_explicit_sort(client, three_indexed_records):
#     response = client.get("/records?sort=mostrecent", headers=HEADERS)

#     assert response.json['hits']['hits'][0] == 1
#     assert response.json['hits']['hits'][1] == 2
#     assert response.json['hits']['hits'][2] == 3
""

# def test_explicit_sort_reversed(client, three_indexed_records):
#     response = client.get("/records?sort=-mostrecent", headers=HEADERS)

#     assert response.json['hits']['hits'][0] == 1
#     assert response.json['hits']['hits'][1] == 2
#     assert response.json['hits']['hits'][2] == 3

# configuration
# def test_sort_by_callable_field()
# mostviewed=dict(
#             fields=['-_stats.version_views'],
#             title='Most viewed',
#             default_order='asc',
#             order=1,
#         ),
# def test_sort_by_multiple_fields()

# def test_search_configuration(client, three_indexed_records):
# app.config["RECORDS_REST_SORT_OPTIONS"] = dict(
#     myindex=dict(
#         myfield=dict(
#             fields=['field1', '-field2'],
#         )
#     ),
# )
# app.config["RECORDS_REST_DEFAULT_SORT"] = dict(
#     myindex=dict(
#         query='-myfield',
#         noquery='myfield',
#     ),
# )


#
# 3- links are generated
#

def test_sort_in_links_if_and_only_if_sort_in_url(
        client, three_indexed_records):
    response = client.get(
        "/records?sort=mostrecent", headers=HEADERS
    )

    response_links = response.json["links"]
    expected_links = {
        "self": (
            "https://localhost:5000/api/records?size=25&page=1&sort=mostrecent"
        ),
        "next": (
            "https://localhost:5000/api/records?size=25&page=2&sort=mostrecent"
        ),
    }
    # NOTE: This is done so that we only test for pagination links
    for key, url in expected_links.items():
        assert url == response_links[key]

    response = client.get(
        "/records", headers=HEADERS
    )

    response_links = response.json["links"]
    expected_links = {
        "self": (
            "https://localhost:5000/api/records?size=25&page=1"
        ),
        "next": (
            "https://localhost:5000/api/records?size=25&page=2"
        ),
    }
    # NOTE: This is done so that we only test for pagination links
    for key, url in expected_links.items():
        assert url == response_links[key]


def test_searchstring_is_preserved(client, three_indexed_records):
    response = client.get(
        "/records?q=Romans+story&sort=mostrecent",
        headers=HEADERS
    )

    response_links = response.json["links"]
    expected_links = {
        "self": (
            "https://localhost:5000/api/records?size=25&page=1&sort=mostrecent"
            "&q=Romans+story"
        ),
        "next": (
            "https://localhost:5000/api/records?size=25&page=2&sort=mostrecent"
            "&q=Romans+story"
        ),
    }
    # NOTE: This is done so that we only test for pagination links
    for key, url in expected_links.items():
        assert url == response_links[key]


# Q: Should sort key be in output if key is undefined in backend?
