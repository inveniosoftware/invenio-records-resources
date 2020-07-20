# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

import json

from flask import jsonify, make_response, request, url_for
from invenio_rest.errors import RESTException, RESTValidationError
from werkzeug.routing import BuildError


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

#
# Query
#


class InvalidDataRESTError(RESTException):
    """Invalid request body."""

    code = 400
    description = "Could not load data."


def _flatten_marshmallow_errors(errors, parents=()):
    """Flatten marshmallow errors."""
    res = []
    for field, error in errors.items():
        if isinstance(error, list):
            res.append(
                dict(
                    parents=parents,
                    field=field,
                    message=" ".join(str(x) for x in error),
                )
            )
        elif isinstance(error, dict):
            res.extend(
                _flatten_marshmallow_errors(error, parents=parents + (field,))
            )
    return res


class MarshmallowErrors(RESTValidationError):
    """Marshmallow validation errors.

    Responsible for formatting a JSON response to a user when a validation
    error happens.
    """

    def __init__(self, errors):
        """Store marshmallow errors."""
        self._it = None
        self.errors = _flatten_marshmallow_errors(errors)
        super(MarshmallowErrors, self).__init__()

    def __str__(self):
        """Print exception with errors."""
        return "{base}. Encountered errors: {errors}".format(
            base=super(MarshmallowErrors, self).__str__(), errors=self.errors
        )

    def __iter__(self):
        """Get iterator."""
        self._it = iter(self.errors)
        return self

    def next(self):
        """Python 2.7 compatibility."""
        return self.__next__()  # pragma: no cover

    def __next__(self):
        """Get next file item."""
        return next(self._it)

    def get_body(self, environ=None):
        """Get the request body."""
        body = dict(status=self.code, message=self.get_description(environ),)

        if self.errors:
            body["errors"] = self.errors

        return json.dumps(body)
