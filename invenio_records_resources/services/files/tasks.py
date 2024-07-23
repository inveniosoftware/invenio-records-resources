# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2024 CERN.
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


@shared_task(ignore_result=True)
def fetch_file(service_id, record_id, file_key):
    """Fetch file from external storage."""
    try:
        service = current_service_registry.get(service_id)
        transfer_metadata = service.get_transfer_metadata(
            system_identity, record_id, file_key
        )
        source_url = transfer_metadata["uri"]
        # download file
        # verify=True for self signed certificates by default
        with requests.get(source_url, stream=True, allow_redirects=True) as response:
            # save file
            service.set_file_content(
                system_identity,
                record_id,
                file_key,
                response.raw,  # has read method
            )
            transfer_metadata.pop("uri")
            service.update_transfer_metadata(
                system_identity, record_id, file_key, transfer_metadata
            )
            # commit file
            service.commit_file(system_identity, record_id, file_key)

    except FileKeyNotFoundError as e:
        current_app.logger.error(e)
    except Exception as e:
        current_app.logger.error(e)
        traceback.print_exc()
        raise
