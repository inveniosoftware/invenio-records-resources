# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Celery tasks for async processing."""

import arrow
from celery import shared_task
from invenio_access.permissions import system_identity

from .proxies import current_notifications_registry, current_service_registry


@shared_task(ignore_result=True)
def extract_file_metadata(service_id, record_id, file_key):
    """Process file."""
    service = current_service_registry.get(service_id)
    service.extract_file_metadata(system_identity, record_id, file_key)


@shared_task(ignore_result=True)
def send_change_notifications(record_type, records_info):
    """Execute the handlers set up for a record_type update."""
    task_start = arrow.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")

    handlers = current_notifications_registry.get(record_type)
    for notif_handler in handlers:
        notif_handler(system_identity, record_type, records_info, task_start)
