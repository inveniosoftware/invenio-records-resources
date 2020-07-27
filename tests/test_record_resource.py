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
import os

import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_view
from invenio_pidstore.minters import recid_minter_v2
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, \
    RecordIdentifier
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_pidstore.proxies import current_pidstore

from invenio_records_resources.services.errors import PermissionDeniedError

HEADERS = {"content-type": "application/json", "accept": "application/json"}


@pytest.fixture(scope="function")
def app_with_custom_minter(app):
    """Application providing a minter creating unregistered pid values."""

    def custom_minter(record_uuid, data):
        """Custom class to mint a new pid in `NEW` state."""

        class CustomRecordIdProvider(RecordIdProvider):
            default_status = PIDStatus.NEW

            @classmethod
            def create(cls, object_type=None, object_uuid=None, **kwargs):
                # Request next integer in recid sequence.
                kwargs['pid_value'] = str(RecordIdentifier.next())
                kwargs.setdefault('status', cls.default_status)
                return super(RecordIdProvider, cls).create(
                    object_type=object_type, object_uuid=object_uuid, **kwargs)

        provider = CustomRecordIdProvider.create(
            object_type='rec', object_uuid=record_uuid)
        data['recid'] = provider.pid.pid_value
        return provider.pid

    current_pidstore.minters['recid_v2'] = custom_minter
    yield app

    current_pidstore.minters['recid_v2'] = recid_minter_v2


def test_create_read_record(client, input_record, es_clear):
    """Test record creation."""
    # Create new record
    response = client.post(
        "/records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201
    response_fields = response.json.keys()
    fields_to_check = ['pid', 'metadata', 'revision',
                       'created', 'updated', 'links']
    for field in fields_to_check:
        assert field in response_fields

    # Save record pid for posterior operations
    recid = response.json["pid"]
    # Read the record
    response = client.get("/records/{}".format(recid), headers=HEADERS)
    assert response.status_code == 200
    assert response.json["pid"] == recid  # Check it matches with the original

    response_fields = response.json.keys()
    fields_to_check = ['pid', 'metadata', 'revision',
                       'created', 'updated', 'links']
    for field in fields_to_check:
        assert field in response_fields


def test_create_search_record(client, input_record, es_clear):
    """Test record search."""
    # Search records, should return empty
    response = client.get("/records", headers=HEADERS)
    assert response.status_code == 200

    # Create dummy record to test search
    response = client.post(
        "/records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201

    # Search content of record, should return the record
    response = client.get("/records?q=story", headers=HEADERS)
    assert response.status_code == 200

    # Search for something non-existent, should return empty
    response = client.get("/records?q=notfound", headers=HEADERS)
    assert response.status_code == 200


def test_create_delete_record(client, input_record, es_clear):
    """Test record deletion."""
    # Create dummy record to test delete
    response = client.post(
        "/records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201
    recid = response.json["pid"]

    # Update the record
    updated_record = input_record
    updated_record["title"] = "updated title"
    response = client.put("/records/{}".format(recid), headers=HEADERS,
                          data=json.dumps(updated_record))
    assert response.status_code == 200

    # Delete the record
    response = client.delete("/records/{}".format(recid),
                             headers=HEADERS)
    assert response.status_code == 204


def test_create_update_record(client, input_record, es_clear):
    """Test record update."""
    # Create dummy record to test update
    response = client.post(
        "/records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201
    recid = response.json["pid"]

    # Update the record
    new_title = "updated title"
    input_record["title"] = new_title
    response = client.put("/records/{}".format(recid), headers=HEADERS,
                          data=json.dumps(input_record))
    assert response.status_code == 200

    # Read the record
    response = client.get("/records/{}".format(recid), headers=HEADERS)
    assert response.status_code == 200
    assert response.json["metadata"]["title"] == new_title


# # FIXME: Currently throws exception. Error handling needed
# def test_create_invalid_record(client, input_record):
#     """Test invalid record creation."""
#     input_record.pop("title")  # Remove a required field of the record

#     response = client.post(
#         "/records", headers=HEADERS, data=json.dumps(input_record)
#     )

#     # TODO: Assert


def test_read_deleted_record(client, input_record, es_clear):
    """Test read a deleted record."""
    # Create dummy record to test delete
    response = client.post(
        "/records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201
    recid = response.json["pid"]

    # Delete the record
    response = client.delete("/records/{}".format(recid),
                             headers=HEADERS)
    assert response.status_code == 204

    # Read the deleted record
    response = client.get("/records/{}".format(recid), headers=HEADERS)
    assert response.status_code == 410
    assert response.json['message'] == "The record has been deleted."


def test_read_record_with_non_existing_pid(client, input_record, es_clear):
    """Test read a record with a non existing pid."""

    response = client.get("/records/randomid", headers=HEADERS)
    assert response.status_code == 404

    assert response.json["status"] == 404
    assert response.json['message'] == "The pid does not exist."


def test_read_record_with_unregistered_pid(app_with_custom_minter,
                                           input_record, es_clear):
    """Test read a record with an unregistered pid."""

    client = app_with_custom_minter.test_client()
    # Create dummy record with unregistered pid value
    response = client.post(
        "/records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201
    recid = response.json["pid"]

    response = client.get("/records/{}".format(recid), headers=HEADERS)
    assert response.status_code == 404

    assert response.json["status"] == 404
    assert response.json['message'] == "The pid is not registered."


def test_read_record_with_redirected_pid(client, input_record, es_clear):
    """Test read a record with a redirected pid."""

    # Create dummy record
    response = client.post(
        "/records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201
    pid1 = PersistentIdentifier.get("recid", response.json["pid"])

    # Create another dummy record
    response = client.post(
        "/records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201
    pid2 = PersistentIdentifier.get("recid", response.json["pid"])

    # redirect pid1 to pid2
    pid1.redirect(pid2)

    response = client.get("/records/{}".format(pid1.pid_value),
                          headers=HEADERS)
    assert response.status_code == 301

    assert response.json["status"] == 301
    assert response.json['message'] == "Moved Permanently."


def test_read_record_with_different_type_of_redirected_pid(
        app, client, input_record, monkeypatch, es_clear):
    """Test read a record with a redirected pid that is of different type."""

    # monkeypatch the `testing` flask attribute so exceptions
    # are not reraised
    monkeypatch.setattr(app, "testing", False)

    # Create dummy record
    response = client.post(
        "/records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201
    pid1 = PersistentIdentifier.get("recid", response.json["pid"])
    assert pid1.pid_type == "recid"

    # Create another dummy record
    response = client.post(
        "/records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201
    pid2 = PersistentIdentifier.get("recid", response.json["pid"])
    assert pid2.pid_type == "recid"

    # change the pid2 pid_type
    pid2.pid_type = 'random'

    # redirect pid1 to pid2
    pid1.redirect(pid2)

    response = client.get("/records/{}".format(pid1.pid_value),
                          headers=HEADERS)
    assert response.status_code == 500

    assert response.json["status"] == 500
    assert "internal error" in response.json["message"]
