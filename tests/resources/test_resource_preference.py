# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test preference."""

from unittest import mock

from invenio_records_resources.resources.records import resource


def test_get_search_preference(app, client, headers, monkeypatch):
    _mock = mock.MagicMock(return_value="test")
    monkeypatch.setattr(resource, "search_preference", _mock)

    h = {**headers, "User-Agent": "Chrome"}
    environ = {"REMOTE_ADDR": "1.2.3.4"}
    r = client.get("/mocks", headers=h, environ_overrides=environ)

    assert resource.search_preference.called
