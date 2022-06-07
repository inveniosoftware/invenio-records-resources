# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from flask import Flask

from invenio_records_resources import InvenioRecordsResources


def test_version():
    """Test version import."""
    from invenio_records_resources import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioRecordsResources(app)
    assert "invenio-records-resources" in app.extensions

    app = Flask("testapp")
    ext = InvenioRecordsResources()
    assert "invenio-records-resources" not in app.extensions
    ext.init_app(app)
    assert "invenio-records-resources" in app.extensions
