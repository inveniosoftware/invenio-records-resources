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

from elasticsearch_dsl import Q

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


def terms_filter(field):
    """Create a term filter.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """
    def inner(values):
        return Q('terms', **{field: values})
    return inner


class SearchEngine():
    """Search records with specific configuration."""

    def __init__(self, search_cls, query_interpreter=QueryInterpreter(),
                 options=None, *args, **kwargs):
        """Constructor."""
        self.search = search_cls(*args, **kwargs)
        self.query_interpreter = query_interpreter
        self.options = options or {}

    def execute_search(self, query):
        """Executes an already parsed query."""
        return self.search.query(query).execute()

    def extra_search(self, extras):
        """Add extra args to search object.

        :params extras: dict of extra arguments
        """
        if extras:
            self.search = self.search.extra(**extras)

        return self

    def facet_search(self, faceting):
        """Facet search object.

        :params faceting: faceting URL args
        """
        faceting_options = self.options.get("faceting", {})

        # Aggregations
        aggregations = faceting_options.get("aggs", {})
        for name, agg in aggregations.items():
            # `aggs[]=` mutates `self.search`
            self.search.aggs[name] = agg if not callable(agg) else agg()

        faceting_args = faceting or {}
        faceting_args = {
            k: v if type(v) is list else [v] for k, v in faceting_args.items()
        }

        # Post filtering
        post_filters = faceting_options.get("post_filters", {})
        for name, filter_factory in post_filters.items():
            facet_values = faceting_args.get(name)
            if facet_values:
                self.search = self.search.post_filter(
                    filter_factory(facet_values)
                )

        return self

    def filter_facets(self, faceting):
        """Filter faceting and keep keys in faceting options only.

        :params faceting: faceting URL args
        """
        faceting_options = self.options.get("faceting", {})
        post_filters = faceting_options.get("post_filters", {})
        return {k: v for k, v in faceting.items() if k in post_filters}

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

    def paginate_search(self, pagination):
        """Paginate search object.

        :params pagination: pagination URL args
        """
        if pagination:
            self.search = self.search[
                pagination["from_idx"]: pagination["to_idx"]
            ]

        return self

    def parse_query(self, querystring):
        """Parses the query based on the interpreter."""
        return self.query_interpreter.parse(querystring)

    def preference_search(self, preference):
        """Avoid query bounce problem on search object.

        :params preference: bool set with_preference_param() or not
        """
        if preference:
            self.search = self.search.with_preference_param()

        return self

    def search_arguments(self, pagination=None, preference=True, version=True,
                         sorting=None, faceting=None, extras=None):
        """Adds arguments to the search object."""
        self.preference_search(preference)
        self.version_search(version)
        self.paginate_search(pagination)
        self.sort_search(sorting)
        self.facet_search(faceting)
        self.extra_search(extras)
        return self

    def sort_search(self, sorting):
        """Sort search object.

        :params sorting: sorting URL args
        """
        if sorting:
            sort_by_options = self.get_sort_by_options(sorting)
            sort_args = [
                eval_field(f, sorting.get("reverse"))
                for f in sort_by_options.get('fields', [])
            ]
            self.search = self.search.sort(*sort_args)

        return self

    def version_search(self, version):
        """Version search object.

        :params version: bool add document version to ES response
        """
        if version:
            self.search = self.search.params(version=True)

        return self
