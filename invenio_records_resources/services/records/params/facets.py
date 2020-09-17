# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query interpreter API."""

from elasticsearch_dsl import Q

from .base import ParamInterpreter


class FacetsParam(ParamInterpreter):
    """Evaluate the 'sort' parameter."""

    def __init__(self, options=None):
        """Initialize with the query parser."""
        self.options = options or None

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        # TODO
        return search
