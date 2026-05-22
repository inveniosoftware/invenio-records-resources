# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2020-2025 Northwestern University.
# SPDX-License-Identifier: MIT

"""Index field tests."""

from invenio_search.engine import dsl

from tests.mock_module.api import Record


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
