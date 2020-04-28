# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from flask import Flask

from invenio_resources import InvenioResources


def test_version():
    """Test version import."""
    from invenio_resources import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioResources(app)
    assert "invenio-resources" in app.extensions

    app = Flask("testapp")
    ext = InvenioResources()
    assert "invenio-resources" not in app.extensions
    ext.init_app(app)
    assert "invenio-resources" in app.extensions
