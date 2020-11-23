# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
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
from mock_module.service import FileService, Service


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
    return Service()


@pytest.fixture(scope='module')
def file_service(appctx):
    """File service instance."""
    return FileService()


@pytest.fixture()
def example_record(app, db):
    """Example record."""
    record = Record.create({}, metadata={'title': 'Test'})
    db.session.commit()
    return record


@pytest.fixture()
def example_file_record(db):
    """Example record."""
    record = RecordWithFile.create({}, metadata={'title': 'Test'})
    record.commit()
    db.session.commit()
    return record


@pytest.fixture(scope="function")
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        'metadata': {
            'title': 'Test',
        },
    }
