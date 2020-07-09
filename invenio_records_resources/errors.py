# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

import json

from invenio_rest.errors import RESTException, RESTValidationError

# TODO: Revise this

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
