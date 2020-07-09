# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs"""

import json

HEADERS = {"content-type": "application/json", "accept": "application/json"}


def test_create_read_record(client, minimal_record):
    """Test record creation."""
    # Create new record
    response = client.post(
        "/api/records_v2", headers=HEADERS, data=json.dumps(minimal_record)
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
    response = client.get("/api/records_v2/{}".format(recid), headers=HEADERS)
    assert response.status_code == 200
    assert response.json["pid"] == recid  # Check it matches with the original

    response_fields = response.json.keys()
    fields_to_check = ['pid', 'metadata', 'revision',
                       'created', 'updated', 'links']
    for field in fields_to_check:
        assert field in response_fields


# TODO: Fix and uncomment
# def test_create_search_record(client, minimal_record):
#     """Test record search."""
#     # Search records, should return empty
#     # response = client.get("/api/records_v2", headers=HEADERS)
#     # assert response.status_code == 200

#     # Create dummy record to test search
#     response = client.post(
#         "/api/records_v2", headers=HEADERS, data=json.dumps(minimal_record)
#     )
#     assert response.status_code == 200
#     print("response.json", response.json)

#     # Search content of record, should return the record
#     response = client.get("/api/records_v2?q=story", headers=HEADERS)
#     assert response.status_code == 200

#     # Search for something non-existent, should return empty
#     response = client.get("/api/records_v2?q=notfound", headers=HEADERS)
#     assert response.status_code == 200


def test_create_delete_record(client, minimal_record):
    """Test record deletion."""
    # Create dummy record to test delete
    response = client.post(
        "/api/records_v2", headers=HEADERS, data=json.dumps(minimal_record)
    )
    assert response.status_code == 200
    recid = response.json["pid"]

    # Update the record
    updated_record = minimal_record
    updated_record["titles"][0]["title"] = "updated title"
    response = client.put("/api/records_v2/{}".format(recid), headers=HEADERS,
                          data=json.dumps(updated_record))
    assert response.status_code == 200

    # Delete the record
    response = client.delete("/api/records_v2/{}".format(recid),
                             headers=HEADERS)
    assert response.status_code == 204


def test_create_update_record(client, minimal_record):
    """Test record update."""
    # Create dummy record to test update
    response = client.post(
        "/api/records_v2", headers=HEADERS, data=json.dumps(minimal_record)
    )
    assert response.status_code == 200
    recid = response.json["pid"]

    # Update the record
    new_title = "updated title"
    minimal_record["titles"][0]["title"] = new_title
    response = client.put("/api/records_v2/{}".format(recid), headers=HEADERS,
                          data=json.dumps(minimal_record))
    assert response.status_code == 200

    # Read the record
    response = client.get("/api/records_v2/{}".format(recid), headers=HEADERS)
    assert response.status_code == 200
    assert response.json["metadata"]["titles"][0]["title"] == new_title
