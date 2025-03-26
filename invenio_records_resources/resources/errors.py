# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Common Errors handling for Resources."""

from json import JSONDecodeError

import marshmallow as ma
from flask import jsonify, make_response, request, url_for
from flask_resources import HTTPJSONException, create_error_handler
from invenio_i18n import lazy_gettext as _
from invenio_pidstore.errors import (
    PIDAlreadyExists,
    PIDDeletedError,
    PIDDoesNotExistError,
    PIDRedirectedError,
    PIDUnregistered,
)
from invenio_records.systemfields.relations import (
    InvalidCheckValue,
    InvalidRelationValue,
)
from invenio_search.engine import search
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.routing import BuildError

from ..errors import validation_error_to_list_errors
from ..services.errors import (
    FacetNotFoundError,
    FailedFileUploadException,
    FileKeyNotFoundError,
    FilesCountExceededException,
    PermissionDeniedError,
    QuerystringValidationError,
    RecordPermissionDeniedError,
    RevisionIdMismatchError,
)


class HTTPJSONValidationException(HTTPJSONException):
    """HTTP exception serializing to JSON and reflecting Marshmallow errors."""

    description = "A validation error occurred."

    def __init__(self, exception):
        """Constructor."""
        super().__init__(code=400, errors=validation_error_to_list_errors(exception))


class HTTPJSONSearchRequestError(HTTPJSONException):
    """HTTP exception responsible for mapping search engine errors."""

    causes_responses = {
        "query_shard_exception": (400, _("Invalid query string syntax.")),
        "query_parsing_exception": (400, _("Invalid query string syntax.")),
        "illegal_argument_exception": (500, _("Misconfigured search.")),
    }

    def __init__(self, error):
        """Parse RequestError."""
        cause_types = {c["type"] for c in error.info["error"]["root_cause"]}
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
                request.url_rule.endpoint, pid_value=e.destination_pid.pid_value
            )
            data = dict(
                status=301,
                message="Moved Permanently.",
                location=location,
            )
            response = make_response(jsonify(data), data["status"])
            response.headers["Location"] = location
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
                description=_("Invalid querystring parameters."),
            )
        ),
        PermissionDeniedError: create_error_handler(
            HTTPJSONException(
                code=403,
                description=_("Permission denied."),
            )
        ),
        RecordPermissionDeniedError: create_error_handler(
            HTTPJSONException(
                code=403,
                description=_("Permission denied."),
            )
        ),
        PIDDeletedError: create_error_handler(
            HTTPJSONException(
                code=410,
                description=_("The record has been deleted."),
            )
        ),
        PIDAlreadyExists: create_error_handler(
            HTTPJSONException(
                code=400,
                description=_("The persistent identifier is already registered."),
            )
        ),
        PIDDoesNotExistError: create_error_handler(
            HTTPJSONException(
                code=404,
                description=_("The persistent identifier does not exist."),
            )
        ),
        PIDUnregistered: create_error_handler(
            HTTPJSONException(
                code=404,
                description=_("The persistent identifier is not registered."),
            )
        ),
        PIDRedirectedError: create_pid_redirected_error_handler(),
        NoResultFound: create_error_handler(
            HTTPJSONException(
                code=404,
                description=_("Not found."),
            )
        ),
        FacetNotFoundError: create_error_handler(
            lambda e: HTTPJSONException(
                code=404,
                description=_(
                    "Facet %(vocabulary_id)s not found.", vocabulary_id=e.vocabulary_id
                ),
            )
        ),
        FileKeyNotFoundError: create_error_handler(
            lambda e: HTTPJSONException(
                code=404,
                description=str(e),
            )
        ),
        JSONDecodeError: create_error_handler(
            HTTPJSONException(
                code=400,
                description=_("Unable to decode JSON data in request body."),
            )
        ),
        InvalidRelationValue: create_error_handler(
            HTTPJSONException(
                code=400,
                description=_("Not a valid value."),
            )
        ),
        InvalidCheckValue: create_error_handler(
            HTTPJSONException(
                code=400,
                description=_("Not a valid value."),
            )
        ),
        search.exceptions.RequestError: create_error_handler(
            lambda e: HTTPJSONSearchRequestError(e)
        ),
        FailedFileUploadException: create_error_handler(
            HTTPJSONException(
                code=400,
                description=_("The file upload transfer failed, please try again."),
            )
        ),
        FilesCountExceededException: create_error_handler(
            HTTPJSONException(
                code=400,
                description=_(
                    "Uploading selected files will result in exceeding the max amount per record."
                ),
            )
        ),
    }
