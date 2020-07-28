# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from urllib.parse import urlencode

from flask import current_app

from .pagination import PagedIndexes
from .schemas.url_args import DEFAULT_MAX_RESULTS


def _base_url(
        scheme="https", host=None, path="/", querystring="", api=False):
    """Creates the URL for API and UI endpoints."""
    assert path.startswith("/")
    path = f"/api{path}" if api else path
    host = host or current_app.config['SERVER_HOSTNAME']
    return f"{scheme}://{host}{path}{querystring}"


class ResourceUnitLinks:
    """Constructor."""

    def __init__(self, route, pid_value):
        """Constructor."""
        self.route = route
        self.pid_value = pid_value

    def links(self):
        """Returns dict of links for the record associated with the pid."""
        path = self.route.replace("<pid_value>", self.pid_value)
        self_api_link = _base_url(path=path, api=True)
        # TODO: The UI route should be passed down and used. It may not be the
        #       same as the API item_route URL
        self_html_link = _base_url(path=path, api=False)

        return {
            "self": self_api_link,
            "self_html": self_html_link,
        }


class ResourceListLinks:
    """Constructor."""

    def __init__(self, route, search_args):
        """Constructor."""
        self.route = route
        self.search_args = search_args

    def _api_search_url(self, querystring_seq):
        querystring = "?" + urlencode(querystring_seq)
        return _base_url(api=True, path=self.route, querystring=querystring)

    def _list_querystring(self, size, page, q=None):
        """Returns ordered sequence of querystring arguments."""
        # NOTE: We order the querystring with the search query at the end,
        #       to make the URLs consistent and more easy to change
        querystring_seq = [
            ("size", size),
            ("page", page),
        ]
        if q:
            querystring_seq.append(("q", q))

        return querystring_seq

    def _links_self(self):
        """Return link to self."""
        querystring_seq = self._list_querystring(
            self.search_args["size"],
            self.search_args["page"],
            self.search_args["q"]
        )
        return self._api_search_url(querystring_seq)

    def _links_prev(self):
        """Returns link to previous page of search results.

        Returns None if there is no previous page.
        """
        size = self.search_args["size"]
        page = self.search_args["page"]
        prev_page = PagedIndexes(size, page, DEFAULT_MAX_RESULTS).prev_page()

        if prev_page:
            querystring_seq = self._list_querystring(
                size,
                page - 1,
                self.search_args["q"]
            )
            return self._api_search_url(querystring_seq)
        else:
            return None

    def _links_next(self):
        """Returns link to next page of search results.

        Returns None if there is no next page.
        """
        size = self.search_args["size"]
        page = self.search_args["page"]
        next_page = PagedIndexes(size, page, DEFAULT_MAX_RESULTS).next_page()

        if next_page:
            querystring_seq = self._list_querystring(
                size,
                page + 1,
                self.search_args["q"]
            )
            return self._api_search_url(querystring_seq)
        else:
            return None

    def links(self):
        """Returns links associated with this resource list."""
        _links = {
            "self": self._links_self(),
        }
        if self._links_prev():
            _links["prev"] = self._links_prev()
        if self._links_next():
            _links["next"] = self._links_next()
        return _links
