# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Search engine DSL response class for adding a facets property."""

from invenio_search.engine import dsl


class FacetsResponse(dsl.response.Response):
    """Search response class that adds a facet property.

    Provides a ``facets`` and ``labelled_facets`` property that you can use
    to access facets with or without labels.

    .. code-block:: python

        result = search.execute()

        for name, data in result.labelled_facets:
            data.label  # <-- label for aggregation
            for b in data.buckets:
                b.label  # <-- label for one bucket
                b.key
                b.is_selected  # <-- true if result are filtered on this bucket

    """

    @classmethod
    def create_response_cls(cls, facets_param):
        """Create a custom class with a reference to the facets param."""
        # Not pretty, but we don't have control over the instantiation of the
        # class.

        # _facets_param is a reference to an instance of a FacetsParam
        # interpreter which holds data such as selected values and which
        # filters was applied.
        class FacetsResponseForRequest(cls):
            _facets_param = facets_param

        return FacetsResponseForRequest

    def _iter_facets(self):
        # _facets_param instance is added to _search by the FacetsParam.apply
        for name, facet in self._facets_param.facets.items():
            yield (
                name,
                facet,
                getattr(self.aggregations, name),
                self._facets_param.selected_values.get(name, []),
            )

    @property
    def facets(self):
        """Unlabelled facets."""
        if not hasattr(self, "_facets"):
            super().__setattr__("_facets", dsl.AttrDict({}))

            try:
                for name, facet, data, selection in self._iter_facets():
                    self._facets[name] = facet.get_values(data, selection)
            except AttributeError:
                # Attribute errors are masked by AttrDict, so we reraise as a
                # different exception.
                raise RuntimeError("Failed to created facets due to attribute error.")

        return self._facets

    @property
    def labelled_facets(self):
        """Labelled facets."""
        if not hasattr(self, "_labelled_facets"):
            super().__setattr__("_labelled_facets", dsl.AttrDict({}))

            try:
                for name, facet, data, selection in self._iter_facets():
                    self._labelled_facets[name] = facet.get_labelled_values(
                        data, selection
                    )
            except AttributeError:
                # Attribute errors are masked by AttrDict, so we reraise as a
                # different exception.
                raise RuntimeError(
                    "Failed to build labelled facets due to attribute error."
                )

        return self._labelled_facets
