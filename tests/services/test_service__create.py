# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service create tests."""


def test_default(app, service, identity_simple, input_data):
    """Create a record (normal path)."""
    item = service._create(service.record_cls, identity_simple, input_data)

    assert item.id
    assert item.data["metadata"]


def test_allow_missing_required(app, service, identity_simple):
    """Create a record without required fields."""
    input_data = {
        'metadata': {}
    }

    item = service._create(
        service.record_cls, identity_simple, input_data, raise_errors=False
    )
    item_dict = item.to_dict()

    assert item.id
    assert item_dict["metadata"] == {}
    assert item_dict["errors"]["metadata"]["title"]


def test_allow_missing_required_incorrect_field(app, service, identity_simple):
    input_data = {
        'metadata': {
            'title': 10,
        },
    }

    item = service._create(
        service.record_cls, identity_simple, input_data, raise_errors=False
    )
    item_dict = item.to_dict()

    assert item.id
    assert item_dict["metadata"] == {}
    assert item_dict["errors"]["metadata"]["title"]
