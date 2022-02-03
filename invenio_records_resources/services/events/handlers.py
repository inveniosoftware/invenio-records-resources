# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Event handlers module."""

from dataclasses import asdict
from datetime import datetime

from celery import shared_task
from flask import current_app

from .bus import EventBus


def _handlers_for_key(key):
    """Returns the handlers for a key."""
    config_handlers = current_app.config["RECORDS_RESOURCES_EVENTS_HANDLERS"]
    keys_parts = key.split(".")

    event_handlers = []
    curr_key = ""
    for part in keys_parts:
        curr_key = f"{curr_key}.{part}"
        try:
            event_handlers.expand(config_handlers[curr_key])
        except KeyError:
            current_app.logger.warning(f"No handler for key {curr_key}")

    return event_handlers


def _handle_event(event, handler=None):
    """Executes the handlers configured for an event."""
    handlers = _handlers_for_key(event.handling_key)

    for handler in handlers:
        func = handler
        async_ = True
        if isinstance(handler, tuple):
            func = handler[0]
            async_ = handler[1]

        if async_:
            func.delay(**asdict(event))
        else:
            func(**asdict(event))

        # audit logging
        current_app.logger.info(
            f"{event.type}-{event.action} handled successfully."
        )


@shared_task(ignore_result=True)
def handle_events(queue_name=None, max_events=1000, ttl=300):
    """Handle events queue.

    :param max_events: maximum number of events to process by the task.
    :param ttl: time to live (in seconds) for the task.
    """
    bus = EventBus(queue_name)
    start = datetime.timestamp(datetime.now())
    end = start
    spawn_new = False
    with bus.active_consumer() as consumer:
        while max_events > 0 and (start + ttl) > end:
            spawn_new = False
            event = consumer.consume()  # blocking
            _handle_event(event)  # execute all handlers
            end = datetime.timestamp(datetime.now())
            spawn_new = True

    if spawn_new:
        handle_events.delay(
            queue_name=queue_name, max_events=max_events, ttl=ttl
        )
