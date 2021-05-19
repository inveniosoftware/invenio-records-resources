# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Celery tasks for async processing."""

from celery import shared_task
from invenio_access.permissions import system_identity

from .proxies import current_service_registry


@shared_task(ignore_result=True)
def extract_file_metadata(service_id, record_id, file_key):
    """Process file."""
    service = current_service_registry.get(service_id)
    service.extract_file_metadata(record_id, file_key, system_identity)
