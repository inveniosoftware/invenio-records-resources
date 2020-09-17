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


class QueryParser:
    """Parse query string into a Elasticsearch DSL Q object."""

    def __init__(self, identity=None):
        """Initialise the parser."""
        self.identity = identity

    def parse(self, query_str):
        """Parse the query."""
        return Q('query_string', query=query_str)


class QueryStrParam(ParamInterpreter):
    """Evaluate the 'q' parameter."""

    def __init__(self, parser_cls=QueryParser):
        """Initialize with the query parser."""
        self.parser_cls = parser_cls

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        query_str = params.get('q')
        if query_str is None:
            return search

        try:
            query = self.parser_cls(identity).parse(query_str)
            return search.query(query)
        except SyntaxError:
            # TOOD: raise a proper type of exception
            raise Exception("Failed to parse query.")
