# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Example resource."""

from invenio_records_resources.resources import FileActionResource, \
    FileActionResourceConfig, FileResource, FileResourceConfig, \
    RecordResource, RecordResourceConfig

from .schema import FileLinksSchema, FilesLinksSchema, RecordLinksSchema, \
    SearchLinksSchema


class CustomRecordResourceConfig(RecordResourceConfig):
    """Custom record resource configuration."""

    list_route = "/mocks"
    item_route = f"{list_route}/<pid_value>"

    links_config = {
        "record": RecordLinksSchema,
        "search": SearchLinksSchema,
        "file": FileLinksSchema,
        "files": FilesLinksSchema,
    }


class CustomRecordResource(RecordResource):
    """Custom record resource"."""

    default_config = CustomRecordResourceConfig


class CustomFileResourceConfig(FileResourceConfig):
    """Custom file resource configuration."""

    item_route = "/mocks/<pid_value>/files/<key>"
    list_route = "/mocks/<pid_value>/files"

    links_config = {
        "file": FileLinksSchema,
        "files": FilesLinksSchema,
    }


class CustomFileResource(FileResource):
    """Custom file resource."""

    default_config = CustomFileResourceConfig


class CustomFileActionResourceConfig(FileActionResourceConfig):
    """Custom file action resource config."""

    list_route = "/mocks/<pid_value>/files/<key>/<action>"

    links_config = {
        "file": FileLinksSchema,
        "files": FilesLinksSchema,
    }


class CustomFileActionResource(FileActionResource):
    """Custom file action resource."""

    default_config = CustomFileActionResourceConfig
