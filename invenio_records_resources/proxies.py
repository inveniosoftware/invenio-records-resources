# SPDX-FileCopyrightText: 2021-2022 CERN.
# SPDX-FileCopyrightText: 2025 CESNET.
# SPDX-License-Identifier: MIT

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

current_transfer_registry = LocalProxy(
    lambda: current_app.extensions["invenio-records-resources"].transfer_registry
)
