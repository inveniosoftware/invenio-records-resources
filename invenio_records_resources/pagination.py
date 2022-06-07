# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Utility class for doing pagination calculations."""


class Pagination:
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

    def valid(self):
        """Returns True if valid, False if not."""
        pre_condition = 1 <= self.size and 1 <= self.page
        return pre_condition and 0 <= self.from_idx < self.max_results

    @property
    def prev_page(self):
        """Returns the previous Page or None if no previous Page."""
        page = Pagination(self.size, self.page - 1, self.max_results)
        return page if page.valid() else None

    @property
    def has_prev(self):
        """True of pagination has a prev page."""
        return self.prev_page is not None

    @property
    def next_page(self):
        """Returns the previous Page or None if no previous Page."""
        page = Pagination(self.size, self.page + 1, self.max_results)
        return page if page.valid() else None

    @property
    def has_next(self):
        """True of pagination has a next page."""
        return self.next_page is not None

    @property
    def from_idx(self):
        """Start index (with respect to all results) for this page."""
        return (self.page - 1) * self.size

    @property
    def to_idx(self):
        """Stop index (with respect to all results) for this page.

        The index is non-inclusive.
        """
        return min(self.page * self.size, self.max_results)
