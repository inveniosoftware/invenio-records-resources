# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pagination functionality."""

from urllib.parse import urlencode

from .schema import DEFAULT_MAX_RESULTS, PagedIndexes, SearchURLArgsSchemaV1
from .urlutils import base_url


class PaginationLinks:
    """Helper for making pagination links (self, prev, next)."""

    def __init__(self, route, search_args):
        """Constructor."""
        self.route = route
        # TODO: Why do we need a schema to dump the search args?
        self.search_args = SearchURLArgsSchemaV1().dump(search_args)

    def links(self):
        """Returns links associated with this resource list."""
        pagination = PagedIndexes(
            self.search_args["size"],
            self.search_args["page"],
            DEFAULT_MAX_RESULTS
        )

        _links = {
            "self": self._page_link(0)
        }

        if pagination.prev_page:
            _links["prev"] = self._page_link(-1)
        if pagination.next_page:
            _links["next"] = self._page_link(+1)

        return _links

    def _page_link(self, offset):
        """Makes a page link to an offset from the current page."""
        querystring_seq = self._ordered_querystring()
        querystring_seq[1] = (
            querystring_seq[1][0], querystring_seq[1][1] + offset
        )

        return base_url(
            path=self.route,
            querystring="?" + urlencode(querystring_seq)
        )

    def _ordered_querystring(self):
        """Returns the ordered list of querystring key, values."""
        # NOTE: We order the querystring with the search query at the end,
        #       to make the URLs consistent and more easy to change
        return [
            (k, self.search_args[k]) for k in ["size", "page", "sort", "q"]
            if k in self.search_args and self.search_args[k]
        ]
