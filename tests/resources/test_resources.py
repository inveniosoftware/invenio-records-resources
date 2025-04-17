# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests."""

import json

from tests.mock_module.api import Record


def test_simple_flow(app, client, input_data, headers):
    """Test a simple REST API flow."""
    idx = "records-record-v1.0.0"
    h = headers

    # Create a record
    res = client.post("/mocks", headers=h, data=json.dumps(input_data))
    assert res.status_code == 201
    id_ = res.json["id"]
    assert res.json["metadata"] == input_data["metadata"]

    # Read the record
    res = client.get(f"/mocks/{id_}", headers=h)
    assert res.status_code == 200
    assert res.json["metadata"] == input_data["metadata"]

    # TODO: Should this be part of the service? we don't know the index easily
    Record.index.refresh()

    # Search it
    res = client.get("/mocks", query_string={"q": f"id:{id_}"}, headers=h)
    assert res.status_code == 200
    assert res.json["hits"]["total"] == 1
    assert res.json["hits"]["hits"][0]["metadata"] == input_data["metadata"]
    data = res.json["hits"]["hits"][0]
    data["metadata"]["title"] = "New title"

    # Update it
    res = client.put(f"/mocks/{id_}", headers=h, data=json.dumps(data))
    assert res.status_code == 200
    assert res.json["metadata"]["title"] == "New title"

    # Delete it
    res = client.delete(f"/mocks/{id_}")
    assert res.status_code == 204
    assert res.get_data(as_text=True) == ""

    Record.index.refresh()

    # Try to get it again
    res = client.get(f"/mocks/{id_}", headers=h)
    assert res.status_code == 410

    # Try to get search it again
    res = client.get("/mocks", query_string={"q": f"id:{id_}"}, headers=h)
    assert res.status_code == 200
    assert res.json["hits"]["total"] == 0


def test_search_suggest(client, input_data, headers, service, monkeypatch):
    # Create a record
    res = client.post("/mocks", headers=headers, data=json.dumps(input_data))
    assert res.status_code == 201
    Record.index.refresh()

    # Suggest it
    res = client.get("/mocks", query_string={"suggest": "te"}, headers=headers)
    assert res.status_code == 200
    assert res.json["hits"]["total"] == 1

    # It's an error to provide both "suggest" and "q"
    res = client.get(
        "/mocks", query_string={"suggest": "te", "q": "te"}, headers=headers
    )
    assert res.status_code == 400

    # It's an error to use suggest if the suggest parser is not configured
    monkeypatch.setattr(service.config.search, "suggest_parser_cls", None)
    res = client.get("/mocks", query_string={"suggest": "te"}, headers=headers)
    assert res.status_code == 400


def test_query_errors(app, client, input_data, headers):
    """Test query syntax related errors."""
    h = headers
    res = client.post("/mocks", headers=h, data=json.dumps(input_data))
    assert res.status_code == 201

    # Test invalid Lucene syntax is properly handled
    res = client.get("/mocks", query_string={"q": "id~:"}, headers=h)
    assert res.status_code == 200

    # Valid Lucene syntax, but invalid in Elasticsearch
    res = client.get("/mocks", query_string={"q": "id:test!"}, headers=h)
    assert res.status_code == 400
    assert res.json["message"] == "Invalid query string syntax."


def test_api_errors(app, client, input_data, headers):
    """Test REST API errors."""
    h = headers

    # Create a record
    res = client.post("/mocks", headers=h, data=json.dumps(input_data))
    assert res.status_code == 201
    id_ = res.json["id"]
    assert res.json["metadata"] == input_data["metadata"]

    # Test PIDDoesNotExistError
    res = client.get("/mocks/n0t3x-15t1n", headers=h)
    assert res.status_code == 404
    assert res.json["message"] == "The persistent identifier does not exist."

    # Test QuerystringValidationError
    res = client.get("/mocks?page=2000", headers=headers)
    assert res.status_code == 400
    assert res.json["message"] == "Invalid querystring parameters."

    # Delete it
    res = client.delete(f"/mocks/{id_}")
    assert res.status_code == 204
    assert res.get_data(as_text=True) == ""

    Record.index.refresh()

    # Test PIDDeletedError
    res = client.get(f"/mocks/{id_}", headers=h)
    assert res.status_code == 410
    assert res.json["message"] == "The record has been deleted."

    # Test JSONDecodeError
    wrong_data = '"metadata": {"title": "Test"}}'
    res = client.post("/mocks", headers=h, data=wrong_data)
    assert res.status_code == 400
    assert res.json["message"] == "Unable to decode JSON data in request body."
