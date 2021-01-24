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
from flask_resources.parsers import HeadersParser, URLArgsParser
from flask_resources.resources import ResourceConfig
from flask_resources.serializers import JSONSerializer
from invenio_pidstore.errors import PIDAlreadyExists, PIDDeletedError, \
    PIDDoesNotExistError, PIDRedirectedError, PIDUnregistered
from marshmallow.exceptions import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from ...services.errors import PermissionDeniedError, \
    QuerystringValidationError, RevisionIdMismatchError
from ..errors import HTTPJSONValidationException
from .errors import create_pid_redirected_error_handler
from .response import RecordResponse
from .schemas_header import RequestHeadersSchema
from .schemas_links import ItemLinksSchema, SearchLinksSchema
from .schemas_url_args import SearchURLArgsSchema


class RecordResourceConfig(ResourceConfig):
    """Record resource config."""

    list_route = "/records"
    item_route = f"{list_route}/<pid_value>"

    links_config = {
        "record": ItemLinksSchema.create(template='/api/records/{pid_value}'),
        "search": SearchLinksSchema.create(template='/api/records{?params*}'),
    }

    request_url_args_parser = {
        "search": URLArgsParser(SearchURLArgsSchema)
    }

    request_headers_parser = {
        "search": HeadersParser(None),
        "update": HeadersParser(RequestHeadersSchema),
        "delete": HeadersParser(RequestHeadersSchema),
    }

    response_handlers = {
        "application/json": RecordResponse(JSONSerializer())
    }

    error_map = {
        ValidationError: create_errormap_handler(
            lambda e: HTTPJSONValidationException(e)
        ),
        RevisionIdMismatchError: create_errormap_handler(
            lambda e: HTTPJSONException(
                code=412,
                description=e.description,
            )
        ),
        QuerystringValidationError: create_errormap_handler(
            HTTPJSONException(
                code=400,
                description="Invalid querystring parameters.",
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
        PIDAlreadyExists: create_errormap_handler(
            HTTPJSONException(
                code=400,
                description="The persistent identifier is already registered.",
            )
        ),
        PIDDoesNotExistError: create_errormap_handler(
            HTTPJSONException(
                code=404,
                description="The persistent identifier does not exist.",
            )
        ),
        PIDUnregistered: create_errormap_handler(
            HTTPJSONException(
                code=404,
                description="The persistent identifier is not registered.",
            )
        ),
        PIDRedirectedError: create_pid_redirected_error_handler(),
        NoResultFound: create_errormap_handler(
            HTTPJSONException(
                code=404,
                description="Not found.",
            )
        ),
    }
