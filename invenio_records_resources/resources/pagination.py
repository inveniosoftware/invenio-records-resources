# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pagination functionality."""


class PagedIndexes:
    """Encapsulates pagination logic."""

    def __init__(self, size, page, max_results):
        """Constructor.

        :param size: int >= 1
        :param page: int >= 1
        :param max_results: int >= 1

        These are validated in valid().
        """
        self.size = size
        self.page = page
        self.max_results = max_results

    @property
    def from_idx(self):
        """Start index (with respect to all results) for this page."""
        return (self.page - 1) * self.size

    def valid(self):
        """Returns True if valid, False if not."""
        pre_condition = (
            self.size >= 1 and self.page >= 1 and self.max_results >= 1
        )
        return pre_condition and 0 <= self.from_idx < self.max_results

    @property
    def to_idx(self):
        """Stop index (with respect to all results) for this page.

        The index is non-inclusive.
        """
        return min(self.page * self.size, self.max_results)

    def prev_page(self):
        """Returns the previous Page or None if no previous Page."""
        page = PagedIndexes(self.size, self.page - 1, self.max_results)
        return page if page.valid() else None

    def next_page(self):
        """Returns the previous Page or None if no previous Page."""
        page = PagedIndexes(self.size, self.page + 1, self.max_results)
        return page if page.valid() else None
