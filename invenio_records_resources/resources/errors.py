# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Common Errors handling for Resources."""
from json import JSONDecodeError

import marshmallow as ma
from elasticsearch.exceptions import RequestError
from flask import jsonify, make_response, request, url_for
from flask_babelex import lazy_gettext as _
from flask_resources import HTTPJSONException, create_error_handler
from invenio_pidstore.errors import PIDAlreadyExists, PIDDeletedError, \
    PIDDoesNotExistError, PIDRedirectedError, PIDUnregistered
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.routing import BuildError

from ..errors import validation_error_to_list_errors
from ..services.errors import PermissionDeniedError, \
    QuerystringValidationError, RevisionIdMismatchError


class HTTPJSONValidationException(HTTPJSONException):
    """HTTP exception serializing to JSON and reflecting Marshmallow errors."""

    description = "A validation error occurred."

    def __init__(self, exception):
        """Constructor."""
        super().__init__(
            code=400,
            errors=validation_error_to_list_errors(exception)
        )


class HTTPJSONElasticsearchRequestError(HTTPJSONException):
    """HTTP exception responsible for mapping Elasticsearch errors."""

    causes_responses = {
        'query_shard_exception': (400, _("Invalid query string syntax.")),
        'query_parsing_exception': (400, _("Invalid query string syntax.")),
        'illegal_argument_exception': (500, _("Misconfigured search."))
    }

    def __init__(self, error):
        """Parse RequestError."""
        cause_types = {c['type'] for c in error.info['error']['root_cause']}
        for t in cause_types:
            if t in self.causes_responses:
                code, msg = self.causes_responses[t]
                super().__init__(code=code, description=msg)
                return
        super().__init__(code=500, description=_("Internal server error"))


def create_pid_redirected_error_handler():
    """Creates an error handler for `PIDRedirectedError` error."""

    def pid_redirected_error_handler(e):
        try:
            # Check that the source pid and the destination pid are of the same
            # pid_type
            assert e.pid.pid_type == e.destination_pid.pid_type
            # Redirection works only for the item route of the format
            # `/records/<pid_value>`
            location = url_for(
                request.url_rule.endpoint,
                pid_value=e.destination_pid.pid_value
            )
            data = dict(
                status=301,
                message='Moved Permanently.',
                location=location,
            )
            response = make_response(jsonify(data), data['status'])
            response.headers['Location'] = location
            return response
        except (AssertionError, BuildError, KeyError):
            raise e

    return pid_redirected_error_handler


class ErrorHandlersMixin:
    """Mixin to define common error handlers."""

    error_handlers = {
        ma.ValidationError: create_error_handler(
            lambda e: HTTPJSONValidationException(e)
        ),
        RevisionIdMismatchError: create_error_handler(
            lambda e: HTTPJSONException(
                code=412,
                description=e.description,
            )
        ),
        QuerystringValidationError: create_error_handler(
            HTTPJSONException(
                code=400,
                description="Invalid querystring parameters.",
            )
        ),
        PermissionDeniedError: create_error_handler(
            HTTPJSONException(
                code=403,
                description="Permission denied.",
            )
        ),
        PIDDeletedError: create_error_handler(
            HTTPJSONException(
                code=410,
                description="The record has been deleted.",
            )
        ),
        PIDAlreadyExists: create_error_handler(
            HTTPJSONException(
                code=400,
                description="The persistent identifier is already registered.",
            )
        ),
        PIDDoesNotExistError: create_error_handler(
            HTTPJSONException(
                code=404,
                description="The persistent identifier does not exist.",
            )
        ),
        PIDUnregistered: create_error_handler(
            HTTPJSONException(
                code=404,
                description="The persistent identifier is not registered.",
            )
        ),
        PIDRedirectedError: create_pid_redirected_error_handler(),
        NoResultFound: create_error_handler(
            HTTPJSONException(
                code=404,
                description="Not found.",
            )
        ),
        JSONDecodeError: create_error_handler(
            HTTPJSONException(
                code=400,
                description="Unable to decode JSON data in request body.",
            )
        ),
        RequestError: create_error_handler(
            lambda e: HTTPJSONElasticsearchRequestError(e)
        ),
    }
