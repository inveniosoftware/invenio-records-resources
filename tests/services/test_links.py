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
from flask_principal import Identity


@pytest.fixture()
def identity_no_need():
    """Simple identity fixture without needs."""
    i = Identity(1)
    return i


def test_links(service, identity_simple, example_record, es):
    """Test record links creation."""
    pid_value = str(example_record.id)

    # NOTE: We are testing linker.links() as opposed to record_unit.links
    #       because the former is used in all RecordService methods (not just
    #       create)
    links = service.linker.links(
        "record",
        identity_simple,
        pid_value=pid_value,
        record=example_record,
    )

    expected_links = {
        "self": f"https://localhost:5000/api/records/{pid_value}",
        "delete": f"https://localhost:5000/api/records/{pid_value}",
        # NOTE: Generate the link even if no file(s) for now
        "files": f"https://localhost:5000/api/records/{pid_value}/files",
    }

    assert expected_links == links


# TODO: example record needs to be permission aware
@pytest.mark.skip()
def test_links_with_permissions(service, identity_no_need, example_record, es):
    """Test record links creation with permissions."""
    pid_value = str(example_record.id)

    links = service.linker.links(
        "record",
        identity_no_need,  # an identity without access
        pid_value=pid_value,
        record=example_record,
    )

    assert {} == links
