# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Errors."""

from flask_resources.errors import HTTPJSONException


class ActionNotImplementedError(HTTPJSONException):
    """Command not implemented error."""

    code = 500
    description = "Action not implemented."

    def __init__(self, cmd_name=None, **kwargs):
        """Constructor."""
        super(ActionNotImplementedError, self).__init__(**kwargs)
        if cmd_name:
            self.description = f"Action '{cmd_name}' not implemented."
