# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs"""

import json

import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_view

from invenio_records_resources.service.errors import PermissionDeniedError

HEADERS = {"content-type": "application/json", "accept": "application/json"}


def test_create_read_record(client, input_record):
    """Test record creation."""
    # Create new record
    response = client.post(
        "/records_v2", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 200
    response_fields = response.json.keys()
    fields_to_check = ['pid', 'metadata', 'revision',
                       'created', 'updated', 'links']
    for field in fields_to_check:
        assert field in response_fields

    # Save record pid for posterior operations
    recid = response.json["pid"]

    # Read the record
    response = client.get("/records_v2/{}".format(recid), headers=HEADERS)
    assert response.status_code == 200
    assert response.json["pid"] == recid  # Check it matches with the original

    response_fields = response.json.keys()
    fields_to_check = ['pid', 'metadata', 'revision',
                       'created', 'updated', 'links']
    for field in fields_to_check:
        assert field in response_fields


# This test DOES NOT clean after itself. It works every time on CI,
# because the CI creates a new container for each test run. It will work
# once locally, but fail on subsequent run.
# TODO: FIX to make it clean up itself. Adding es_clear didn't work
# def test_create_search_record(client, input_record):
#     """Test record search."""
#     # Search records, should return empty
#     response = client.get("/records_v2", headers=HEADERS)
#     assert response.status_code == 200

#     # Create dummy record to test search
#     response = client.post(
#         "/records_v2", headers=HEADERS, data=json.dumps(input_record)
#     )
#     assert response.status_code == 200
#     print("response.json", response.json)

#     # Search content of record, should return the record
#     response = client.get("/records_v2?q=story", headers=HEADERS)
#     assert response.status_code == 200

#     # Search for something non-existent, should return empty
#     response = client.get("/records_v2?q=notfound", headers=HEADERS)
#     assert response.status_code == 200


def test_create_delete_record(client, input_record):
    """Test record deletion."""
    # Create dummy record to test delete
    response = client.post(
        "/records_v2", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 200
    recid = response.json["pid"]

    # Update the record
    updated_record = input_record
    updated_record["title"] = "updated title"
    response = client.put("/records_v2/{}".format(recid), headers=HEADERS,
                          data=json.dumps(updated_record))
    assert response.status_code == 200

    # Delete the record
    response = client.delete("/records_v2/{}".format(recid),
                             headers=HEADERS)
    assert response.status_code == 204


def test_create_update_record(client, input_record):
    """Test record update."""
    # Create dummy record to test update
    response = client.post(
        "/records_v2", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 200
    recid = response.json["pid"]

    # Update the record
    new_title = "updated title"
    input_record["title"] = new_title
    response = client.put("/records_v2/{}".format(recid), headers=HEADERS,
                          data=json.dumps(input_record))
    assert response.status_code == 200

    # Read the record
    response = client.get("/records_v2/{}".format(recid), headers=HEADERS)
    assert response.status_code == 200
    assert response.json["metadata"]["title"] == new_title


# # FIXME: Currently throws exception. Error handling needed
# def test_create_invalid_record(client, input_record):
#     """Test invalid record creation."""
#     input_record.pop("title")  # Remove a required field of the record

#     response = client.post(
#         "/records_v2", headers=HEADERS, data=json.dumps(input_record)
#     )

#     # TODO: Assert
