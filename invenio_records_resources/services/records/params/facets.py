# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C)      2022 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets parameter interpreter API."""

from copy import deepcopy

from ..facets import FacetsResponse
from .base import ParamInterpreter


class FacetsParam(ParamInterpreter):
    """Evaluate facets."""

    def __init__(self, config):
        """Initialise the facets interpreter."""
        super().__init__(config)
        self.selected_values = {}
        self._filters = {}

    @property
    def facets(self):
        """Get the defined facets."""
        return deepcopy(self.config.facets)

    def add_filter(self, name, values):
        """Add a filter for a facet."""
        self.selected_values[name] = values
        f = self.facets[name].add_filter(values)
        if f is not None:
            self._filters[name] = f

    @staticmethod
    def _combine(filters):
        """Combine filters with AND. Returns None if no filters."""
        if not filters:
            return None
        combined = filters[0]
        for f in filters[1:]:
            combined &= f
        return combined

    def filter(self, search):
        """Apply filters on the search."""
        if not self._filters:
            return search

        facets = self.facets
        post_filters, direct_filters = [], []
        for name, f in self._filters.items():
            if getattr(facets[name], "post_filter", True):
                post_filters.append(f)
            else:
                direct_filters.append(f)

        direct = self._combine(direct_filters)
        if direct is not None:
            search = search.filter(direct)
        post = self._combine(post_filters)
        if post is not None:
            search = search.post_filter(post)

        return search

    def aggregate(self, search):
        """Add aggregations representing the facets."""
        facets = self.facets
        for name, facet in facets.items():
            if name in self.selected_values and hasattr(facet, "prepare_aggregation"):
                facet.prepare_aggregation(list(self.selected_values[name]))
            agg = facet.get_aggregation()
            search.aggs.bucket(name, agg)
        return search

    def apply(self, identity, search, params):
        """Evaluate the facets on the search."""
        # Add filters
        facets_values = params.pop("facets", {})
        for name, values in facets_values.items():
            if name in self.facets:
                self.add_filter(name, values)

        # Customize response class to add a ".facets" property.
        search = search.response_class(FacetsResponse.create_response_cls(self))

        # Build search
        search = self.aggregate(search)
        search = self.filter(search)

        # Update params
        params.update(self.selected_values)

        return search
