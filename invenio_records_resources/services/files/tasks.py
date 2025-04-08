# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2024 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files tasks."""

import traceback

import requests
from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity

from ...proxies import current_service_registry
from ...services.errors import FileKeyNotFoundError
from .transfer.constants import LOCAL_TRANSFER_TYPE


@shared_task(ignore_result=True)
def fetch_file(service_id, record_id, file_key):
    """Fetch file from external storage."""
    try:
        service = current_service_registry.get(service_id)
        transfer_metadata = service.get_transfer_metadata(
            system_identity, record_id, file_key
        )
        source_url = transfer_metadata["url"]
        # download file
        # verify=True for self signed certificates by default
        try:
            with requests.get(
                source_url, stream=True, allow_redirects=True
            ) as response:
                # save file
                if response.status_code != 200:
                    current_app.logger.error(
                        f"Failed to fetch file from {source_url} with status code {response.status_code}"
                    )
                    transfer_metadata["error"] = response.text
                    service.update_transfer_metadata(
                        system_identity, record_id, file_key, transfer_metadata
                    )
                    return
                service.set_file_content(
                    system_identity,
                    record_id,
                    file_key,
                    response.raw,  # has read method
                )
                transfer_metadata.pop("url")
                transfer_metadata["type"] = LOCAL_TRANSFER_TYPE
                service.update_transfer_metadata(
                    system_identity, record_id, file_key, transfer_metadata
                )
                # commit file
                service.commit_file(system_identity, record_id, file_key)
        except Exception as e:
            current_app.logger.error(e)
            transfer_metadata["error"] = str(e)
            service.update_transfer_metadata(
                system_identity, record_id, file_key, transfer_metadata
            )
            return

    except FileKeyNotFoundError as e:
        current_app.logger.error(e)

    except Exception as e:
        current_app.logger.error(e)
        traceback.print_exc()
        # do not raise an exception as we want the task to be marked as errored
        raise
