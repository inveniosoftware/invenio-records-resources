# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""
from uuid import uuid4

import pytest
from flask_principal import Identity, Need, UserNeed
from mock_module.api import Record, RecordWithFile
from mock_module.config import ServiceConfig

from invenio_records_resources.services import RecordService


@pytest.fixture(scope='module')
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method='system_role', value='any_user'))
    return i


@pytest.fixture(scope='module')
def service(appctx):
    """Service instance."""
    return RecordService(ServiceConfig)


@pytest.fixture(scope="function")
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        'metadata': {
            'title': 'Test',
        },
    }


@pytest.fixture()
def example_record(app, db, input_data):
    """Example data layer record."""
    record = Record.create({}, **input_data)
    db.session.commit()
    return record


@pytest.fixture()
def example_file_record(db, input_data):
    """Example record."""
    record = RecordWithFile.create({}, **input_data)
    record.commit()
    db.session.commit()
    return record
