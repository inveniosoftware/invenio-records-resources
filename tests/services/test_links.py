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
from marshmallow import Schema, fields


class MockResourceRequestCtx:

    url_args = {"q": ""}


class MockRecordLinksSchema(Schema):
    """Schema for a record's links."""

    self = fields.String(default="/api/records/12345-ABCDE")


class MockSearchLinksSchema(Schema):
    """Schema for a search result's links."""

    self = fields.String(default="/api/records?q=")


def test_search_links(app, service, identity_simple, input_data, es_clear):
    """Test record links creation."""
    # Create a dummy record
    item = service.create(identity_simple, input_data)

    resource_requestctx = MockResourceRequestCtx()
    links_config = {
        "record": MockRecordLinksSchema,
        "search": MockSearchLinksSchema
    }
    result_list = service.search(
        identity=identity_simple,
        params=resource_requestctx.url_args,
        links_config=links_config,
    ).to_dict()

    expected_search_links = {
        "self": "/api/records?q="
    }

    assert result_list["links"] == expected_search_links

    expected_item_links = {
        "self": "/api/records/12345-ABCDE"
    }

    for hit in result_list["hits"]["hits"]:
        assert hit["links"] == expected_item_links
