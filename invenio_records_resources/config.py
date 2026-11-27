# SPDX-FileCopyrightText: 2020-2026 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-FileCopyrightText: 2025 CESNET i.a.l.e.
# SPDX-License-Identifier: MIT

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
"""Max entries (files and folders) returned by the container listing API.

It only shortens the response: once reached, the listing stops and is flagged as
``truncated``. It does not change which ZIP files are accepted, nor which entries
can be extracted: see ``RECORDS_RESOURCES_ZIP_MAX_ENTRIES`` for that. Set it to
``None`` to return all entries of the accepted ZIP files.
"""

RECORDS_RESOURCES_ZIP_MAX_HEADER_SIZE = 64 * 1024
"""Max header size of ZIP file that can be preloaded."""

RECORDS_RESOURCES_ZIP_MAX_TOTAL_UNCOMPRESSED = 500 * 1024 * 1024  # 500 MB
"""Max allowed uncompressed size of ZIP."""

RECORDS_RESOURCES_ZIP_MAX_RATIO = 200.0
"""Max allowed compression ratio of an entry inside ZIP file."""

RECORDS_RESOURCES_ZIP_MAX_ENTRIES = 1000
"""Max entries (files and folders) that a ZIP file can contain.

ZIP files with more entries are refused: their content cannot be listed or
extracted, while the file itself can still be downloaded. The refusal of an
uploaded file is saved in its metadata, so raising this value does not apply to
files that were already refused.

It protects the memory of the server, as the whole table of contents of a ZIP is
loaded to open it. For the same reason, the size of the table of contents is
limited to this value multiplied by 512 bytes (about 0.5 MB by default): a ZIP with
very long file names can be refused with fewer entries.

``RECORDS_RESOURCES_ZIP_MAX_LISTING_ENTRIES`` can further limit how many of the
entries of an accepted ZIP are listed.
"""

RECORDS_RESOURCES_ARCHIVE_DOWNLOAD_MAX_SIZE = None
"""Max total file size (bytes) for archive download. ``None`` disables the cap."""

RECORDS_RESOURCES_USE_STAGED_TRANSFER = False
"""Release the database connection while newly initialized files are uploaded."""
