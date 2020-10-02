# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query parameter interpreter API."""

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

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        query_str = params.get('q')
        if not query_str:
            return search

        try:
            parser_cls = self.config.search_query_parser_cls
            query = parser_cls(identity).parse(query_str)
            return search.query(query)
        except SyntaxError:
            # TOOD: raise a proper type of exception
            raise Exception("Failed to parse query.")
