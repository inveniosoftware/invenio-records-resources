# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from datetime import datetime, timezone

import pytest
from invenio_indexer.api import RecordIndexer

from tests.mock_module.api import Record


@pytest.fixture()
def example_data():
    """Example data."""
    return {"metadata": {"title": "Test"}}


@pytest.fixture()
def example_record(db, example_data):
    """Example record."""
    record = Record.create(
        example_data,
        expires_at=datetime(2020, 9, 7, 0, 0, tzinfo=timezone.utc),
    )
    record.commit()
    db.session.commit()
    return record


@pytest.fixture()
def indexer():
    """Indexer instance with correct Record class."""
    return RecordIndexer(record_cls=Record, record_to_index=lambda r: r.index._name)
