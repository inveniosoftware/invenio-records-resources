# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Records Resources module to create REST APIs."""

from . import config
from .registry import NotificationRegistry, ServiceRegistry


class InvenioRecordsResources(object):
    """Invenio-Records-Resources extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.registry = ServiceRegistry()
        self.notification_registry = NotificationRegistry()
        app.extensions["invenio-records-resources"] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("RECORDS_RESOURCES_") or k.startswith("SITE_"):
                app.config.setdefault(k, getattr(config, k))
