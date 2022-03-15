# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""ModelPIDField tests."""

from invenio_db import db
from mock_module.api import Record as RecordBase
from mock_module.models import RecordMetadataWithPID

from invenio_records_resources.records.systemfields import ModelPIDField
from invenio_records_resources.records.systemfields.pid import \
    ModelPIDFieldContext


class Record(RecordBase):
    """Mock record class."""
    model_cls = RecordMetadataWithPID
    pid = ModelPIDField()


def test_class_attribute_access():
    """Test that field is returned."""
    assert isinstance(Record.pid, ModelPIDFieldContext)


def test_record_pid_creation(base_app, db):
    """Test record creation."""
    # without value
    record = Record.create({})
    assert not record.pid
    # with value
    record = Record.create({}, pid="12345-abcde")
    assert record.pid.pid_value == "12345-abcde"


def test_resolver(base_app, db, example_data):
    """Test the resolver."""
    record = Record.create(example_data, pid="12345-abcde")
    resolved_record = Record.pid.resolve("12345-abcde")
    assert resolved_record == example_data
