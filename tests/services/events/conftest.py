# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from datetime import timedelta

import pytest
from kombu import Exchange

from invenio_records_resources.services.events.events import \
    RecordCreatedEvent, RecordEvent


@pytest.fixture(scope="module")
def app_config(app_config):
    """Application configuration."""
    # handlers
    app_config["RECORDS_RESOURCES_EVENTS_HANDLERS"] = {
        RecordEvent.handling_key: [],
        RecordCreatedEvent.handling_key: [
            # (sync_handler_task, True),
            # (explicit_asyn_handler_task, False),
            # implicit_asyn_handler_task,
        ],
    }

    # events queue
    queue_name = "test-events"
    exchange = Exchange(
        queue=queue_name,
        type="direct",
        delivery_mode="persistent",  # in-memory and disk
    )

    app_config["RECORDS_RESOURCES_EVENT_QUEUE"] = queue_name
    app_config["QUEUES_DEFINITIONS"] = [
        {"name": queue_name, "exchange": exchange}
    ]

    # celery config
    app_config["CELERY_ACCEPT_CONTENT"] = ["json", "msgpack", "yaml", "pickle"]
    app_config["CELERYBEAT_SCHEDULE"] = {
        'event_handling': {
            'task': 'invenio_records_resources.services.events.handle_events',
            'schedule': timedelta(minutes=5),
        },
    }

    return app_config
