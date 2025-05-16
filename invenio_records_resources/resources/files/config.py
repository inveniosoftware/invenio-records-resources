# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020-2025 Northwestern University.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File resource configuration."""

from flask_resources import HTTPJSONException, ResourceConfig, create_error_handler

from invenio_records_resources.services.errors import TransferException


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
    }
    error_handlers = {
        **ResourceConfig.error_handlers,
        TransferException: create_error_handler(
            lambda e: HTTPJSONException(
                code=400,
                description=str(e),
            )
        ),
    }
