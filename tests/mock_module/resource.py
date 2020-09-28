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

from uritemplate import URITemplate

from invenio_records_resources.resources import RecordResource, \
    RecordResourceConfig


class ResourceConfig(RecordResourceConfig):
    """Mock service configuration."""

    list_route = "/mocks"
    item_route = f"{list_route}/<pid_value>"

    links_config = {
        "record": {
            "self": URITemplate(f"/api{list_route}{{/pid_value}}"),
        },
        "search": {
            "self": URITemplate(f"/api{list_route}{{?params*}}"),
            "prev": URITemplate(f"/api{list_route}{{?params*}}"),
            "next": URITemplate(f"/api{list_route}{{?params*}}"),
        }
    }


class Resource(RecordResource):
    """Mock service."""

    default_config = ResourceConfig
