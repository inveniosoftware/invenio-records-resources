# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C)      2022 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets parameter interpreter API."""


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
        return self.config.facets

    def add_filter(self, name, values):
        """Add a filter for a facet."""
        # Store selected facet values for later usage
        self.selected_values[name] = values
        # Create a filter for a single facet
        f = self.facets[name].add_filter(values)
        if f is None:
            return
        # Store filter.
        self._filters[name] = f

    def filter(self, search):
        """Apply a post filter on the search."""
        if not self._filters:
            return search

        filters = list(self._filters.values())

        post_filter = filters[0]
        for f in filters[1:]:
            post_filter &= f

        return search.post_filter(post_filter)

    def aggregate(self, search):
        """Add aggregations representing the facets."""
        for name, facet in self.facets.items():
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
