# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

SITE_UI_URL = "https://127.0.0.1:5000"

SITE_API_URL = "https://127.0.0.1:5000/api"

RECORDS_RESOURCES_FILES_ALLOWED_DOMAINS = []
"""Explicitly allowed domains for external file fetching.

Only file URLs from these domains will be allowed to be fetched.
"""

RECORDS_RESOURCES_IMAGE_FORMATS = [".jpg", ".jpeg", ".jp2", ".png", ".tif", ".tiff"]
"""Which image formats to extract metadata for."""

RECORDS_RESOURCES_ALLOW_EMPTY_FILES = True
"""Allow empty files to be uploaded."""

RECORDS_RESOURCES_TRANSFERS = [
    "invenio_records_resources.services.files.transfer.LocalTransfer",
    "invenio_records_resources.services.files.transfer.FetchTransfer",
    "invenio_records_resources.services.files.transfer.RemoteTransfer",
    "invenio_records_resources.services.files.transfer.MultipartTransfer",
]
"""List of transfer classes to register."""


RECORDS_RESOURCES_DEFAULT_TRANSFER_TYPE = "L"
"""Default transfer class to use. 
One of 'L' (local), 'F' (fetch), 'R' (point to remote), 'M' (multipart)."""
