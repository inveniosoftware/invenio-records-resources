# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Search parameter interpreter API."""


class ParamInterpreter:
    """Evaluate a url parameter."""

    def __init__(self, config):
        """Initialise the parameter interpreter."""
        self.config = config

    def apply(self, identity, search, params):
        """Apply the parameters."""
