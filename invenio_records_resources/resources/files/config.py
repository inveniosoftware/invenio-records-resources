# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020-2025 Northwestern University.
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File resource configuration."""

from flask_resources import HTTPJSONException, ResourceConfig, create_error_handler

from invenio_records_resources.services.errors import (
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
