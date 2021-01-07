# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Common Errors handling for Resources."""

from flask_resources.errors import HTTPJSONException

from ..errors import validation_error_to_list_errors


class HTTPJSONValidationException(HTTPJSONException):
    """HTTP exception serializing to JSON and reflecting Marshmallow errors."""

    description = "A validation error occurred."

    def __init__(self, exception):
        """Constructor."""
        super().__init__(
            code=400,
            errors=validation_error_to_list_errors(exception)
        )
