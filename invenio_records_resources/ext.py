# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Records Resources module to create REST APIs."""

from . import config


class InvenioRecordsResources(object):
    """Invenio-Records-Resources extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["invenio-records-resources"] = self

    def init_config(self, app):
        """Initialize configuration."""
        # TODO: This one will actually not load the config specified in
        # config.py because the vars doesn't start with RECORDS_RESOURCES_
        for k in dir(config):
            if k.startswith("RECORDS_RESOURCES_") or k in ['SITE_HOSTNAME']:
                app.config.setdefault(k, getattr(config, k))
