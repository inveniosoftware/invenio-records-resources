# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Agent is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Errors."""

from flask_principal import PermissionDenied
from invenio_rest.errors import RESTException


class PermissionDeniedError(PermissionDenied):
    """Permission denied error."""

    def __init__(self, action):
        """Constructor."""
        pass


class InvalidQueryRESTError(RESTException):
    """Invalid query syntax."""

    code = 400
    description = "Invalid query syntax."
