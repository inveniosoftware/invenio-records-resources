# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Search engine."""

import copy

from .query import QueryInterpreter


def eval_field(field, reverse):
    """Evaluate a field for sorting purpose.

    :param field: Field definition (dict, callable, or string).
    :param reverse: ``True`` if order should be reversed, ``False`` otherwise.
    :returns: Dictionary with the sort field query.
    """
    if isinstance(field, dict):
        if not reverse:
            return field
        else:
            # Field should only have one key and must have an order subkey.
            field = copy.deepcopy(field)
            key = list(field.keys())[0]
            order = field[key]['order']
            field[key]['order'] = 'desc' if order == 'asc' else 'asc'
            return field
    if callable(field):
        return field(reverse)
    else:
        if field.startswith("-"):
            key, ascending = field[1:], False
        else:
            key, ascending = field, True
        ascending = not ascending if reverse else ascending
        return {key: {'order': 'asc' if ascending else 'desc'}}


class SearchEngine():
    """Search records with specific configuration."""

    def __init__(self, search_cls, query_interpreter=QueryInterpreter(),
                 options=None, *args, **kwargs):
        """Constructor."""
        self.search = search_cls(*args, **kwargs)
        self.query_interpreter = query_interpreter
        self.options = options or {}

    def search_arguments(self, pagination=None, preference=True, version=True,
                         sorting=None, extras=None):
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
        if sorting:
            sort_by_options = self.get_sort_by_options(sorting)
            sort_args = [
                eval_field(f, sorting.get("reverse"))
                for f in sort_by_options.get('fields', [])
            ]
            self.search = self.search.sort(*sort_args)

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

    def get_sort_by_options(self, sorting):
        """Return sort_by_options dict."""
        sorting_options = self.options.get("sorting", {})
        sort_by = sorting.get("sort_by")

        if sort_by:
            sort_by_options = sorting_options.get(sort_by, {})
        elif sorting.get("has_q"):
            # TODO: When dealing with config validaion, we can verify that only
            #       one option has default_if_query
            sort_by_options = next((
                options for options in sorting_options.values()
                if "default_if_query" in options
            ), {})
        else:
            sort_by_options = next((
                options for options in sorting_options.values()
                if "default_if_no_query" in options
            ), {})

        return sort_by_options
