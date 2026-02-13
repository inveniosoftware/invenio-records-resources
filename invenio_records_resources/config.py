# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2025 CESNET i.a.l.e.
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


RECORDS_RESOURCES_EXTRACTED_STREAM_CHUNK_SIZE = 64 * 1024
"""Chunk size of extracted stream used in ContainerItemResult.send_file()."""

RECORDS_RESOURCES_ZIP_FORMATS = [".zip"]
"""File extensions interpreted as ZIP files."""

RECORDS_RESOURCES_ZIP_MAX_LISTING_ENTRIES = 1000
"""Max entries returned by the container listing API."""

RECORDS_RESOURCES_ZIP_MAX_HEADER_SIZE = 64 * 1024
"""Max header size of ZIP file that can be preloaded."""

RECORDS_RESOURCES_ZIP_MAX_TOTAL_UNCOMPRESSED = 500 * 1024 * 1024  # 500 MB
"""Max allowed uncompressed size of ZIP."""

RECORDS_RESOURCES_ZIP_MAX_RATIO = 200.0
"""Max allowed compression ratio of an entry inside ZIP file."""

RECORDS_RESOURCES_ZIP_MAX_ENTRIES = 10000
"""Max allowed entries inside ZIP file."""
