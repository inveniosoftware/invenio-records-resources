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
from uritemplate import URITemplate

from ..services.errors import PermissionDeniedError
from .errors import create_pid_redirected_error_handler
from .record_args import SearchURLArgsSchema


class RecordResourceConfig(ResourceConfig):
    """Record resource config."""

    list_route = "/records"
    item_route = f"{list_route}/<pid_value>"

    links_config = {
        "record": {
            "self": URITemplate(f"{list_route}{{/pid_value}}"),
        },
        "search": {
            "self": URITemplate(f"{list_route}{{?params*}}"),
            "prev": URITemplate(f"{list_route}{{?params*}}"),
            "next": URITemplate(f"{list_route}{{?params*}}"),
        }
    }

    request_url_args_parser = {
        "search": ArgsParser(SearchURLArgsSchema)
    }

    response_handlers = {
        "application/json": Response(JSONSerializer())
    }

    error_map = {
        # InvalidQueryError: create_errormap_handler(
        #     HTTPJSONException(
        #         code=400,
        #         description="Invalid query syntax.",
        #     )
        # ),
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
