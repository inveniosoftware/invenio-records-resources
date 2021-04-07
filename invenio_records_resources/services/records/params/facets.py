# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets parameter interpreter API."""

import itertools
import operator

from elasticsearch_dsl import Q

from .base import ParamInterpreter


class FacetsParam(ParamInterpreter):
    """Evaluate facets."""

    def iter_aggs_options(self, options):
        """Iterate over aggregation options."""
        return options.get("aggs", {}).items()

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        options = self.config.facets_options

        # Apply aggregations
        for name, agg in self.iter_aggs_options(options):
            # `aggs[]=` mutates `self.search`
            search.aggs[name] = agg if not callable(agg) else agg()

        # Apply post filters
        facets_args = params.pop("facets", {})
        post_filters = options.get("post_filters", {})

        # List of term queries of all the requested facets
        queries = []

        # Iterating the intersection of facets_args and post_filter keys
        # to avoid key error and invalid facets injection in the request.
        for k in set(facets_args.keys()) & set(post_filters.keys()):
            filter_factory = post_filters[k]
            values = facets_args[k]
            queries.append(filter_factory(values))
            params[k] = values

        if queries:
            final_query = list(itertools.accumulate(queries, operator.or_))[-1]
            search = search.post_filter(final_query)

        return search
