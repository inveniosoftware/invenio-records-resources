# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2020-2025 Northwestern University.
# SPDX-FileCopyrightText: 2025 CESNET i.a.l.e.
# SPDX-License-Identifier: MIT

"""File resource configuration."""

from flask_resources import HTTPJSONException, ResourceConfig, create_error_handler

from ...services.errors import (
    InvalidFileContentError,
    NoExtractorFoundError,
    TransferException,
)


class FileResourceConfig(ResourceConfig):
    """File resource config."""

    blueprint_name = None
    url_prefix = "/records/<pid_value>"
    routes = {
        "list": "/files",
        "item": "/files/<path:key>",
        "item-content": "/files/<path:key>/content",
        "item-multipart-content": "/files/<path:key>/content/<int:part>",
        "item-commit": "/files/<path:key>/commit",
        "list-archive": "/files-archive",
        "list-container": "/files/<path:key>/container",
        "container-item-extract": "/files/<path:key>/container/<path:path>",
    }
    error_handlers = {
        **ResourceConfig.error_handlers,
        TransferException: create_error_handler(
            lambda e: HTTPJSONException(
                code=400,
                description=str(e),
            )
        ),
        NoExtractorFoundError: create_error_handler(
            lambda e: HTTPJSONException(
                code=400,
                description=str(e),
            )
        ),
        InvalidFileContentError: create_error_handler(
            lambda e: HTTPJSONException(
                code=999,  # inspired by linkedin's status code for request denied
                description=str(e),
            )
        ),
    }
