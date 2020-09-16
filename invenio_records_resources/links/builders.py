# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Link builders."""

from .pagination import PaginationLinks
from .urlutils import api_route, base_url


class LinkBuilder:
    """Common interface among most record link builders."""

    def __init__(self, key, route, action, permission_policy):
        """Constructor.

        :param key: Name of the key in the link dictionary being generated.
        :param
        """
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


class ConfigLinkBuilder(LinkBuilder):
    """Link builder which get the route information from the config."""

    key = None
    """Name of the key to use in the link dictionary."""

    action = None
    """Action name for use in the permission policy."""

    route_attr = None
    """Attribute name on the config object to use as route."""

    def __init__(self, config):
        """Initialise the link builder.

        :param config: A resource config.
        """
        super().__init__(
            key=self.key,
            route=api_route(getattr(config, self.route_attr)),
            action=self.action,
            permission_policy=config.permission_policy_cls
        )


class SelfLinkBuilder(ConfigLinkBuilder):
    """Builds a self link."""

    key = "self"
    action = "read"
    route_attr = 'record_route'


class DeleteLinkBuilder(ConfigLinkBuilder):
    """Delete link."""

    key = "delete"
    action = "delete"
    route_attr = 'record_route'


class FilesLinkBuilder(ConfigLinkBuilder):
    """Files link."""

    key = "files"
    action = "delete"
    route_attr = 'record_files_route'


class SearchLinkBuilder(ConfigLinkBuilder):
    """Builds the search links."""

    key = None
    action = "search"
    route_attr = 'record_search_route'

    def route_to_link(self, identity, **kwargs):
        """Converts route to a link."""
        if self.permission_policy(self.action, **kwargs).allows(identity):
            search_args = kwargs["search_args"]
            return PaginationLinks(self.route, search_args).links()
        else:
            return {}
