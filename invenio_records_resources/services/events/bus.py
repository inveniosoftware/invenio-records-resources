# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Events bus module."""

from pickle import dumps, loads

from flask import current_app
from invenio_queues.proxies import current_queues


class EventBus:
    """Event bus."""

    def __init__(self, queue_name=None):
        """Constructor."""
        self._queue_name = queue_name or \
            current_app.config["RECORDS_RESOURCES_EVENTS_QUEUE"]
        self._queue = None

        for name, queue in current_queues.queues.items():
            if name == self._queue_name:
                self._queue = queue
                break

    def publish(self, event):
        """Publish an event to the bus queue."""
        return self._queue.publish([dumps(event)])

    def consume(self):
        """Consume an event from the bus queue."""
        for event in self._queue.consume():  # consume() returns a generator
            yield loads(event)

    def active_consumer(self):
        """Returns a consumer that stays open."""
        # TODO: see usage in handlers.py
        pass
