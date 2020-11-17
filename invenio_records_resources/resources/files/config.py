# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File resource configuration."""

from ..actions import ActionResourceConfig
from ..records import RecordResourceConfig


# NOTE: Inheriting from record resource config enables access to record
#       related configuration such as links
class FileResourceConfig(RecordResourceConfig):
    """Record resource config."""

    item_route = "/records/<pid_value>/files/<key>"
    list_route = "/records/<pid_value>/files"


class FileActionResourceConfig(RecordResourceConfig, ActionResourceConfig):
    """Record resource config."""

    list_route = "/records/<pid_value>/files/<key>/<action>"
    action_commands = {
        'create': {
            'commit': 'commit_file'
        },
        'read': {
            'content': 'retrieve_file'
        },
        'update': {
            'content': 'save_file'
        },
        'delete': {}
    }
