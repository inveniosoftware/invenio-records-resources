# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Helper proxy to the state object."""

from flask import current_app
from werkzeug.local import LocalProxy

current_service_registry = LocalProxy(
    lambda: current_app.extensions["invenio-records-resources"].registry
)
"""Helper proxy to get the current service registry."""


current_notifications_registry = LocalProxy(
    lambda: current_app.extensions["invenio-records-resources"].notification_registry
)
"""Helper proxy to get the current notifications registry."""
