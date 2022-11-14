# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files tasks."""

import requests
from celery import shared_task
from invenio_access.permissions import system_identity

from ...proxies import current_service_registry


@shared_task(ignore_result=True)
def fetch_file(service_id, record_id, file_key):
    """Fetch file from external storage."""
    service = current_service_registry.get(service_id)
    file_record = service.read_file_metadata(system_identity, record_id, file_key)
    source_url = file_record.data["uri"]
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
        # commit file
        service.commit_file(system_identity, record_id, file_key)
