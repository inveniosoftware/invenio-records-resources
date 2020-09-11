# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File resource configuration."""

from flask_resources.resources import ResourceConfig


class FileResourceConfig(ResourceConfig):
    """Record resource config."""

    item_route = "/records/<pid_value>/files/<key>"
    list_route = "/records/<pid_value>/files"


class FileActionResourceConfig(ResourceConfig):
    """Record resource config."""

    # QUESTIONs:
    # 1- Shouldn't the item_route be used for SingletonResource actually?
    #    A change in Flask-Resource would be needed.
    # 2- Should the list_route instead precede download with "actions" to be in
    #    keeping with other actions endpoints?
    list_route = "/records/<pid_value>/files/<key>/download"
