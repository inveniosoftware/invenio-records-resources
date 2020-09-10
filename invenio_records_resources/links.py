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
from .schemas.url_args import DEFAULT_MAX_RESULTS, SearchURLArgsSchemaV1


def api_route(route):
    """Prepends the route with '/api'."""
    assert route.startswith("/")
    return f"/api{route}"


def base_url(
        scheme="https", host=None, path="/", querystring="", api=False):
    """Creates the URL for API and UI endpoints."""
    assert path.startswith("/")
    path = f"/api{path}" if api else path
    host = host or current_app.config['SERVER_HOSTNAME']
    return f"{scheme}://{host}{path}{querystring}"


class ResourceListLinks:
    """Constructor."""

    def __init__(self, route, original_search_args):
        """Constructor."""
        self.route = route
        self.original_search_args = original_search_args
        # NOTE: Dumping removes unknown fields and does some desired
        #       transformations. This is why we add faceting after
        search_args = dict(
            q=original_search_args["querystring"],
            **original_search_args["pagination"],
            **original_search_args["sorting"],
        )
        self.search_args = SearchURLArgsSchemaV1().dump(search_args)
        self.search_args.update(original_search_args["faceting"])

    def _api_search_url(self, querystring_seq):
        querystring = "?" + urlencode(querystring_seq)
        return base_url(path=self.route, querystring=querystring)

    def _ordered_querystring(self):
        """Returns the normalized and ordered list of querystring key, values.

        NOTE: We order the querystring with the search query at the end,
              to make the URLs consistent and more easy to change
        """
        # 1) filter empty (falsey) ["size", "page", "sort", "q"] out
        search_args = {
            k: v for k, v in self.search_args.items()
            if k not in ["size", "page", "sort", "q"] or self.search_args[k]
        }

        # 2) order as ["size", "page", "sort", "<anything else>", "q"]
        # size, page, sort
        querystring_seq = [
            (k, search_args.pop(k))
            for k in ["size", "page", "sort"]
            if k in search_args
        ]
        # pop "q" (may have been filtered out because empty though)
        q = [("q", search_args.pop("q"))] if "q" in search_args else []
        # anything else
        facets_querystring_seq = [
            (facet, value)
            for facet, values in search_args.items()
            for value in values
        ]
        # extend with sorted "<anything else>" + "q"
        querystring_seq += (
            # alphabetically sort by facet and value
            sorted(facets_querystring_seq, key=lambda t: t[0] + t[1]) +
            q
        )

        return querystring_seq

    def _links_self(self):
        """Return link to self."""
        querystring_seq = self._ordered_querystring()
        return self._api_search_url(querystring_seq)

    def _links_prev(self):
        """Returns link to previous page of search results.

        Returns None if there is no previous page.
        """
        size = self.search_args["size"]
        page = self.search_args["page"]
        prev_page = PagedIndexes(size, page, DEFAULT_MAX_RESULTS).prev_page()

        if prev_page:
            querystring_seq = self._ordered_querystring()
            querystring_seq[1] = (
                querystring_seq[1][0], querystring_seq[1][1] - 1
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
            querystring_seq = self._ordered_querystring()
            querystring_seq[1] = (
                querystring_seq[1][0], querystring_seq[1][1] + 1
            )
            return self._api_search_url(querystring_seq)
        else:
            return None

    def links(self):
        """Returns links associated with this resource list."""
        _links = {
            "self": self._links_self(),
        }

        prev_link = self._links_prev()
        if prev_link:
            _links["prev"] = prev_link

        next_link = self._links_next()
        if next_link:
            _links["next"] = next_link

        return _links


class Linker:
    """Linker class.

    Generates all the links for a given namespace.
    """

    def __init__(self, link_builders):
        """Constructor.

        :param link_builders: dict(string, list<LinkBuilder>)
        """
        self.link_builders = link_builders

    def links(self, namespace, identity, **kwargs):
        """Returns dict of links."""
        output_links = {}
        for link_builder in self.link_builders[namespace]:
            link = link_builder.route_to_link(identity, **kwargs)
            output_links.update(link)
        return output_links

    def register_link_builders(self, link_builders):
        """Updates the internal link_builders with new ones."""
        self.link_builders.update(link_builders)


class RecordLinkBuilder:
    """Common interface among most record link builders."""

    def __init__(self, key, route, action, permission_policy):
        """Constructor."""
        self.key = key
        self.route = route
        self.action = action
        self.permission_policy = permission_policy

    def route_to_link(self, identity, **kwargs):
        """Converts route to a link."""
        if self.permission_policy(self.action, **kwargs).allows(identity):
            pid_value = kwargs["pid_value"]
            path = self.route.replace("<pid_value>", pid_value)
            return {self.key: base_url(path=path)}
        else:
            return {}


class RecordSelfLinkBuilder(RecordLinkBuilder):
    """Builds record "self" link."""

    def __init__(self, config):
        """Constructor."""
        super(RecordSelfLinkBuilder, self).__init__(
            key="self",
            route=api_route(config.record_route),
            action="read",
            permission_policy=config.permission_policy_cls
        )


class RecordDeleteLinkBuilder(RecordLinkBuilder):
    """Builds record "delete" link."""

    def __init__(self, config):
        """Constructor."""
        super(RecordDeleteLinkBuilder, self).__init__(
            key="delete",
            route=api_route(config.record_route),
            action="delete",
            permission_policy=config.permission_policy_cls
        )


class RecordFilesLinkBuilder(RecordLinkBuilder):
    """Builds record "files" link."""

    def __init__(self, config):
        """Constructor."""
        super(RecordFilesLinkBuilder, self).__init__(
            key="files",
            route=api_route(config.record_files_route),
            action="read_files",
            permission_policy=config.permission_policy_cls
        )


class RecordSearchLinkBuilder(RecordLinkBuilder):
    """Builds the search links."""

    def __init__(self, config):
        """Constructor."""
        super(RecordSearchLinkBuilder, self).__init__(
            key=None,
            route=api_route(config.record_search_route),
            action="search",
            permission_policy=config.permission_policy_cls
        )

    def route_to_link(self, identity, **kwargs):
        """Converts route to a link."""
        if self.permission_policy(self.action, **kwargs).allows(identity):
            search_args = kwargs["search_args"]
            return ResourceListLinks(self.route, search_args).links()
        else:
            return {}
