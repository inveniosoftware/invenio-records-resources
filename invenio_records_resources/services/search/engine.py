# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Search engine."""

from .query import QueryInterpreter


class SearchEngine():
    """Search records with specific configuration."""

    def __init__(self, search_cls, query_interpreter=QueryInterpreter(),
                 *args, **kwargs):
        """Constructor."""
        self.search = search_cls(*args, **kwargs)
        self.query_interpreter = query_interpreter

    def search_arguments(self, pagination=None, preference=True, version=True,
                         extras=None):
        """Adds arguments to the search object."""
        # Avoid query bounce problem
        if preference:
            self.search = self.search.with_preference_param()
        # Add document version to ES response
        if version:
            self.search = self.search.params(version=True)
        # Add other aguments
        if pagination:
            self.search = self.search[
                pagination["from_idx"]: pagination["to_idx"]
            ]

        # Add extra args
        if extras:
            self.search = self.search.extra(**extras)

        return self

    def parse_query(self, querystring):
        """Parses the query based on the interpreter."""
        return self.query_interpreter.parse(querystring)

    def execute_search(self, query):
        """Executes an already parsed query."""
        return self.search.query(query).execute()
