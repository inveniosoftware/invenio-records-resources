# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File resource configuration."""

from flask_resources import ResourceConfig


class FileResourceConfig(ResourceConfig):
    """File resource config."""

    # Blueprint configuration
    allow_upload = True
    allow_archive_download = True
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
