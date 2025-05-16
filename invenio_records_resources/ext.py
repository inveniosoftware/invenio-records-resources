# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Records Resources module to create REST APIs."""

from functools import cached_property

from invenio_base.utils import obj_or_import_string

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
        self.app = app
        self.init_config(app)
        self.registry = ServiceRegistry()
        self.notification_registry = NotificationRegistry()
        app.extensions["invenio-records-resources"] = self

    @cached_property
    def transfer_registry(self):
        """Return the transfer registry."""
        # imported here to prevent circular imports
        from .services.files.transfer.registry import TransferRegistry

        registry = TransferRegistry(
            self.app.config["RECORDS_RESOURCES_DEFAULT_TRANSFER_TYPE"]
        )
        for transfer_cls in self.app.config["RECORDS_RESOURCES_TRANSFERS"]:
            registry.register(obj_or_import_string(transfer_cls))
        return registry

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("RECORDS_RESOURCES_") or k.startswith("SITE_"):
                app.config.setdefault(k, getattr(config, k))
