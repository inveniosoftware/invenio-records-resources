# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Resource Configuration."""


from flask_resources.errors import HTTPJSONException, create_errormap_handler
from flask_resources.parsers import ArgsParser
from flask_resources.resources import ResourceConfig
from flask_resources.responses import Response
from flask_resources.serializers import JSONSerializer
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError, \
    PIDRedirectedError, PIDUnregistered

from ..linker.schema import SearchURLArgsSchemaV1
from ..search.errors import InvalidQueryError
from ..services.errors import PermissionDeniedError
from .errors import create_pid_redirected_error_handler


class RecordResourceConfig(ResourceConfig):
    """Record resource config."""

    item_route = "/records/<pid_value>"
    list_route = "/records"

    request_url_args_parser = {
        "search": ArgsParser(SearchURLArgsSchemaV1)
    }

    response_handlers = {
        "application/json": Response(JSONSerializer())
    }

    error_map = {
        InvalidQueryError: create_errormap_handler(
            HTTPJSONException(
                code=400,
                description="Invalid query syntax.",
            )
        ),
        PermissionDeniedError: create_errormap_handler(
            HTTPJSONException(
                code=403,
                description="Permission denied.",
            )
        ),
        PIDDeletedError: create_errormap_handler(
            HTTPJSONException(
                code=410,
                description="The record has been deleted.",
            )
        ),
        PIDDoesNotExistError: create_errormap_handler(
            HTTPJSONException(
                code=404,
                description="The pid does not exist.",
            )
        ),
        PIDUnregistered: create_errormap_handler(
            HTTPJSONException(
                code=404,
                description="The pid is not registered.",
            )
        ),
        PIDRedirectedError: create_pid_redirected_error_handler(),
    }
