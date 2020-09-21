# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets parameter interpreter API."""

from .base import ParamInterpreter


class FacetsParam(ParamInterpreter):
    """Evaluate facets."""

    def iter_facet_args(self, params):
        """Iterate over all possible facet arguments."""
        return {
            k: v if type(v) is list else [v] for k, v in (params or {}).items()
        }.items()

    def iter_aggs_options(self, options):
        """Iterate over aggregation options."""
        return options.get("aggs", {}).items()

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        options = self.config.search_facets_options

        # Apply aggregations
        for name, agg in self.iter_aggs_options(options):
            # `aggs[]=` mutates `self.search`
            search.aggs[name] = agg if not callable(agg) else agg()

        # Apply post filters
        post_filters = options.get("post_filters", {})

        for name, facet_values in self.iter_facet_args(params):
            filter_factory = post_filters.get(name)
            if facet_values and filter_factory:
                search = search.post_filter(filter_factory(facet_values))

        return search
