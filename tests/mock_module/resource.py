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

from invenio_records_resources.resources import RecordResource, \
    RecordResourceConfig

from .schema import RecordLinksSchema, SearchLinksSchema


class ResourceConfig(RecordResourceConfig):
    """Mock service configuration."""

    list_route = "/mocks"
    item_route = f"{list_route}/<pid_value>"

    links_config = {
        "record": RecordLinksSchema,
        "search": SearchLinksSchema
    }


class Resource(RecordResource):
    """Mock service."""

    default_config = ResourceConfig
