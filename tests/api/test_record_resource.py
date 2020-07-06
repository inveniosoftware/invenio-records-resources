# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Resources module to create REST APIs"""

import json

HEADERS = {"content-type": "application/json", "accept": "application/json"}


def test_create_read_search_record(client, minimal_record):
    """Test record creation."""
    # Search records, should return empty
    response = client.get("/api/records_v2", headers=HEADERS)
    assert response.status_code == 200

    # Create new record
    response = client.post(
        "/api/records_v2", headers=HEADERS, data=json.dumps(minimal_record)
    )
    assert response.status_code == 200  # Draft created
    recid = response.json["pid"]

    # Search content of record, should return the record
    response = client.get("/api/records_v2?q=story", headers=HEADERS)
    assert response.status_code == 200  # Draft created

    # Search for something non-existent, should return empty
    response = client.get("/api/records_v2?q=notfound", headers=HEADERS)
    assert response.status_code == 200

    # Read the record
    response = client.get("/api/records_v2/{}".format(recid), headers=HEADERS)
    assert response.status_code == 200

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
