# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File resource configuration."""

from flask_resources.deserializers import JSONDeserializer
from flask_resources.loaders import RequestLoader
from flask_resources.serializers import JSONSerializer

from ..actions import ActionResourceConfig
from ..records import RecordResourceConfig
from .loaders import RequestStreamLoader
from .response import RecordFileResponse


# NOTE: Inheriting from record resource config enables access to record
#       related configuration such as links
class FileResourceConfig(RecordResourceConfig):
    """Record resource config."""

    item_route = "/records/<pid_value>/files/<key>"
    list_route = "/records/<pid_value>/files"


class FileActionResourceConfig(RecordResourceConfig, ActionResourceConfig):
    """Record resource config."""

    request_loaders = {
        "application/json": RequestLoader(deserializer=JSONDeserializer()),
        "application/octet-stream": RequestStreamLoader(),
    }

    response_handlers = {
        "application/json": RecordFileResponse(JSONSerializer()),
    }

    list_route = "/records/<pid_value>/files/<key>/<action>"
    action_commands = {
        'create': {
            'commit': 'commit_file'
        },
        'read': {
            'content': 'get_file_content'
        },
        'update': {
            'content': 'set_file_content'
        },
        'delete': {}
    }
