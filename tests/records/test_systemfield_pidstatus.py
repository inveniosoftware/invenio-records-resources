# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""PIDStatusCheckField tests."""

from invenio_pidstore.models import PIDStatus
from mock_module.api import Record

from invenio_records_resources.records.systemfields import PIDStatusCheckField


def test_class_attribute_access():
    """Test that field is returned."""
    assert isinstance(Record.is_published, PIDStatusCheckField)


def test_record_pid_creation(base_app, db):
    """Test record creation."""
    record = Record.create({})
    assert record.is_published is True
    assert record.pid.status == PIDStatus.REGISTERED


def test_record_pid_dump(base_app, db):
    """Test record creation."""
    # Configured to not dump
    record = Record.create({})
    assert "is_published" not in record.dumps()

    # Configure to dump
    class DumpRecord(Record):
        is_published = PIDStatusCheckField(status=PIDStatus.REGISTERED, dump=True)

    record = DumpRecord.create({})
    assert record.dumps()["is_published"] is True
