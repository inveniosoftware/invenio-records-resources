# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File resource configuration."""

from flask_resources.resources import ResourceConfig


class ActionResourceConfig(ResourceConfig):
    """Record resource config."""

    list_route = None  # To force user definition

    action_commands = {
        'create': {},
        'read': {},
        'update': {},
        'delete': {}
    }
