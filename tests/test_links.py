# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test links."""

from invenio_records_resources.links import ResourceUnitLinks


def test_resource_unit_links(app):
    links = ResourceUnitLinks("/records/<pid_value>", "12345-abcde").links()

    expected_links = {
        "self": "https://localhost:5000/api/records/12345-abcde",
        "self_html": "https://localhost:5000/records/12345-abcde",
    }
    assert expected_links == links
