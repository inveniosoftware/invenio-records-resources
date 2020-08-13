# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test links."""

import pytest
from flask_principal import Identity, Need, UserNeed

from invenio_records_resources.services.record import RecordService


@pytest.fixture()
def identity_simple():
    """Simple identity fixture with user 1 and any_user needs."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method='system_role', value='any_user'))
    return i


@pytest.fixture()
def identity_no_need():
    """Simple identity fixture without needs."""
    i = Identity(1)
    return i


def test_record_links(app, identity_simple, input_service_data, es):
    record_service = RecordService()
    record_unit = record_service.create(input_service_data, identity_simple)
    pid_value = record_unit.id

    # NOTE: We are testing linker.links() as opposed to record_unit.links
    #       because the former is used in all RecordService methods (not just
    #       create)
    links = record_service.linker.links(
        "record", identity_simple, pid_value=pid_value,
        record=record_unit.record
    )

    expected_links = {
        "self": f"https://localhost:5000/api/records/{pid_value}",
        "self_html": f"https://localhost:5000/records/{pid_value}",
        "delete": f"https://localhost:5000/api/records/{pid_value}",
    }
    assert expected_links == links


def test_permission_record_links(
        app, identity_no_need, identity_simple, input_service_data, es):
    record_service = RecordService()
    record_unit = record_service.create(input_service_data, identity_simple)
    pid_value = record_unit.id

    links = record_service.linker.links(
        "record", identity_no_need, pid_value=pid_value,
        record=record_unit.record
    )

    assert {} == links
