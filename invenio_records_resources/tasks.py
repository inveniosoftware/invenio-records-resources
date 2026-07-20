# SPDX-FileCopyrightText: 2021-2024 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Celery tasks for async processing."""

from datetime import datetime, timezone

from celery import current_app as current_celery_app
from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_indexer.proxies import current_indexer_registry
from invenio_indexer.tasks import process_bulk_queue
from invenio_pidstore.errors import PIDDoesNotExistError
from sqlalchemy.orm.exc import NoResultFound

from .proxies import current_notifications_registry, current_service_registry


def _published_fallback_service_id(service_id):
    """Map ``draft-*`` file services to their published counterparts."""
    prefix = "draft-"
    if service_id.startswith(prefix):
        return service_id[len(prefix) :]
    return None


@shared_task(ignore_result=True)
def extract_file_metadata(service_id, record_id, file_key):
    """Extract metadata for a file.

    If the draft was published before this task ran, retry on the matching
    published file service (``draft-files`` → ``files``, etc.).
    """
    active_service_id = service_id
    try:
        service = current_service_registry.get(active_service_id)
        try:
            service.extract_file_metadata(system_identity, record_id, file_key)
        except (NoResultFound, PIDDoesNotExistError):
            fallback_service_id = _published_fallback_service_id(service_id)
            if fallback_service_id is None:
                raise

            active_service_id = fallback_service_id
            service = current_service_registry.get(active_service_id)
            service.extract_file_metadata(system_identity, record_id, file_key)
    except Exception as error:
        current_app.logger.exception(
            "Failed to extract file metadata. service_id=%s record_id=%s "
            "file_key=%s exception_type=%s exception=%s",
            active_service_id,
            record_id,
            file_key,
            type(error).__name__,
            error,
        )


@shared_task(ignore_result=True)
def send_change_notifications(record_type, records_info):
    """Execute the handlers set up for a record_type update."""
    task_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")

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
