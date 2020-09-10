# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests.

Test to add:
- Read a tombstone page
- Read with missing permissions
- Read with missing pid


"""

import pytest


@pytest.fixture()
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        'metadata': {
            'title': 'Test'
        },
    }


def test_read(service, example_record, identity_simple):
    """Read a record with the service."""
    recstate = service.read(identity_simple, example_record.id)
    assert recstate.id == str(example_record.id)


def test_create(app, service, identity_simple, input_data):
    """Create a record."""
    recstate = service.create(identity_simple, input_data)
    assert recstate
