# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Event bus test."""

from datetime import datetime
from time import sleep

from invenio_records_resources.services.events import EventBus
from invenio_records_resources.services.events.events import RecordCreatedEvent


def test_bus_publish_consume(app):
    bus = EventBus("test-events")
    event = RecordCreatedEvent(created=datetime.now(), recid="12345-abcde")

    bus.publish(event)
    sleep(10)
    consumed_event = bus.consume()
    assert event == next(consumed_event)
