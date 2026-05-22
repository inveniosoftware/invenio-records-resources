# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-License-Identifier: MIT

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
