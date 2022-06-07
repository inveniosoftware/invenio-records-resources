# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""ModelPIDField tests."""

import pytest
from invenio_records.systemfields import ModelField
from mock_module.api import Record as RecordBase
from mock_module.models import RecordMetadataWithPID

from invenio_records_resources.records.systemfields import ModelPIDField
from invenio_records_resources.records.systemfields.pid import ModelPIDFieldContext


class Record(RecordBase):
    """Mock record class."""

    model_cls = RecordMetadataWithPID
    pid = ModelPIDField()
    pid_status = ModelField()


def test_class_attribute_access():
    """Test that field is returned."""
    assert isinstance(Record.pid, ModelPIDFieldContext)


def test_record_pid_creation(base_app, db):
    """Test record creation."""
    # without value
    record = Record.create({})
    assert not record.pid
    assert not record.pid_status
    # with value
    record = Record.create({}, pid="12345-abcde")
    assert record.pid.pid_value == "12345-abcde"


def test_record_pid_deletion(base_app, db):
    """Test record creation."""
    # create
    record = Record.create({}, pid="12345-abcde")
    assert record.pid.pid_value == "12345-abcde"
    # delete
    record.delete()
    # since there is no status the record is still resolvable
    # but it has no content
    assert {} == Record.pid.resolve("12345-abcde")


def test_resolver(base_app, db, example_data):
    """Test the resolver."""
    record = Record.create(example_data, pid="12345-abcde")
    resolved_record = Record.pid.resolve("12345-abcde")
    assert resolved_record == example_data
