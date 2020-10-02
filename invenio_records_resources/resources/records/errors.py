# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from flask import jsonify, make_response, request, url_for
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
