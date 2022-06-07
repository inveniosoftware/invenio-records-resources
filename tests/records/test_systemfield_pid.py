# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""PIDField tests."""

from datetime import datetime

from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
from mock_module.api import Record
from mock_module.models import RecordMetadata
from sqlalchemy import inspect

from invenio_records_resources.records.api import Record as RecordBase
from invenio_records_resources.records.systemfields import PIDField
from invenio_records_resources.records.systemfields.pid import PIDFieldContext


def test_class_attribute_access():
    """Test that field is returned."""
    assert isinstance(Record.pid, PIDFieldContext)


def test_record_pid_creation(base_app, db):
    """Test record creation."""
    record = Record.create({})
    assert record["id"] == record.pid.pid_value
    assert record["pid"]["pk"] == record.pid.id
    assert record["pid"]["status"] == record.pid.status
    assert record["pid"]["obj_type"] == record.pid.object_type
    assert record["pid"]["pid_type"] == record.pid.pid_type
    assert record.id == record.pid.object_uuid


def test_create_no_provider(base_app, db):
    """Test creation without a provider."""

    class Record(RecordBase):
        model_cls = RecordMetadata
        pid = PIDField()

    record = Record.create({})
    assert record.pid is None

    record.pid = RecordIdProviderV2.create(object_type="rec", object_uuid=record.id).pid

    assert record["id"] == record.pid.pid_value
    assert record["pid"]["pk"] == record.pid.id
    assert record["pid"]["status"] == record.pid.status
    assert record["pid"]["obj_type"] == record.pid.object_type
    assert record["pid"]["pid_type"] == record.pid.pid_type
    assert record.id == record.pid.object_uuid


def test_create_different_key(base_app, db):
    """Test creation with different key."""

    class Record(RecordBase):
        model_cls = RecordMetadata
        pid = PIDField("pid.id", provider=RecordIdProviderV2)

    record = Record.create({})
    assert record["pid"]["id"] == record.pid.pid_value
    assert record["pid"]["pid_type"] == record.pid.pid_type


def test_reading_a_pid(base_app, db):
    """Test reading from dict."""
    record = Record(
        {
            "id": "12345-abcde",
            "pid": {
                "pid_type": "recid",
                "obj_type": "rec",
                "pk": 10,
                "status": "R",
            },
        }
    )
    assert record.pid is not None
    assert record["id"] == record.pid.pid_value
    assert record["pid"]["pk"] == record.pid.id
    assert record["pid"]["status"] == record.pid.status
    assert record["pid"]["obj_type"] == record.pid.object_type
    assert record["pid"]["pid_type"] == record.pid.pid_type


def test_resolver(base_app, db, example_record):
    """Test the resolver."""
    resolved_record = Record.pid.resolve(example_record.pid.pid_value)
    loaded_record = Record.get_record(example_record.id)
    assert resolved_record == loaded_record


def test_session_merge(base_app, db, example_record):
    """Test the session merge."""
    assert inspect(example_record.pid).persistent is True
    assert inspect(example_record.conceptpid).persistent is True

    record = Record.get_record(example_record.id)
    assert inspect(record.pid).persistent is False
    assert inspect(record.conceptpid).persistent is False

    Record.pid.session_merge(record)
    assert inspect(record.pid).persistent is True
    assert inspect(record.conceptpid).persistent is False
