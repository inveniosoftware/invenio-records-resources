# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Celery tasks for async processing."""

import arrow
from celery import current_app as current_celery_app
from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_indexer.proxies import current_indexer_registry
from invenio_indexer.tasks import process_bulk_queue

from .proxies import current_notifications_registry, current_service_registry


@shared_task(ignore_result=True)
def extract_file_metadata(service_id, record_id, file_key):
    """Process file."""
    try:
        service = current_service_registry.get(service_id)
        service.extract_file_metadata(system_identity, record_id, file_key)
    except Exception:
        current_app.logger.exception("Failed to extract file metadata.")


@shared_task(ignore_result=True)
def send_change_notifications(record_type, records_info):
    """Execute the handlers set up for a record_type update."""
    task_start = arrow.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")

    handlers = current_notifications_registry.get(record_type)
    for notif_handler in handlers:
        notif_handler(system_identity, record_type, records_info, task_start)


@shared_task(ignore_result=True)
def manage_indexer_queues():
    """Peeks into queues and spawns bulk indexers."""
    channel = current_celery_app.connection().channel()
    indexers = current_indexer_registry.all()

    for name, indexer in indexers.items():
        queue = indexer.mq_queue.bind(channel)
        _, num_messages, num_consumers = queue.queue_declare()
        max_consumers = current_app.config["INDEXER_MAX_BULK_CONSUMERS"]

        if num_messages > 0 and num_consumers < max_consumers:
            process_bulk_queue.delay(indexer_name=name)
