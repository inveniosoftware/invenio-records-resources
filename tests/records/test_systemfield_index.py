# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Index field tests."""

from invenio_search.engine import dsl
from mock_module.api import Record

from invenio_records_resources.records.systemfields import IndexField


def test_class_attribute_access():
    """Test that field is returned."""
    assert isinstance(Record.index, dsl.Index)


def test_instance_attribute_access(base_app, db):
    """Test record creation."""
    record = Record.create({})
    assert isinstance(record.index, dsl.Index)


def test_refresh(app, db, search):
    """Test record creation."""
    assert Record.index.refresh()
