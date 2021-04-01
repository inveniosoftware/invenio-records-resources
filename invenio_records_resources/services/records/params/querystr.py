# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query parameter interpreter API."""
import re
from functools import partial

from elasticsearch_dsl import Q

from .base import ParamInterpreter


class QueryParser:
    """Parse query string into a Elasticsearch DSL Q object."""

    def __init__(self, identity=None):
        """Initialise the parser."""
        self.identity = identity

    def parse(self, query_str, extra_params):
        """Parse the query."""
        return Q('query_string', query=query_str, **extra_params)


class QueryStrParam(ParamInterpreter):
    """Evaluate the 'q' parameter."""

    def __init__(self, rewrite, boosted_fields, config):
        """."""
        self.rewrite = rewrite
        self.boosted_fields = boosted_fields
        super().__init__(config)

    @classmethod
    def factory(cls, rewrite=None, boosted_fields=None):
        """Create a new query string parameter."""
        return partial(cls, rewrite, boosted_fields)

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        query_str = params.get('q')

        if not query_str:
            return search

        # Adds wildcard (*) to all the words to replace 0 or more characters
        query_str = re.sub(r'(\S+)',
                           lambda m: m.group(1) + '*',
                           query_str)
        extra_params = dict()
        extra_params["default_operator"] = "AND"
        if self.rewrite:
            extra_params["rewrite"] = self.rewrite
        if self.boosted_fields:
            extra_params["fields"] = self.boosted_fields + ["*"]

        try:
            parser_cls = self.config.query_parser_cls
            query = parser_cls(identity).parse(query_str, extra_params)
            return search.query(query)
        except SyntaxError:
            # TOOD: raise a proper type of exception
            raise Exception("Failed to parse query.")
