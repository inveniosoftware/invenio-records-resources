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


def test_get_es_preference(app, client, headers, monkeypatch):
    monkeypatch.setattr(resource, "es_preference", mock.MagicMock(
        return_value='test'))

    h = {**headers, 'User-Agent': 'Chrome'}
    environ = {'REMOTE_ADDR': '1.2.3.4'}
    r = client.get('/mocks', headers=h, environ_overrides=environ)

    assert resource.es_preference.called
