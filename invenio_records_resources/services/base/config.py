# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2020-2022 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service API."""

from invenio_base.utils import load_or_import_from_config
from invenio_records_permissions.policies import BasePermissionPolicy

from .results import ServiceItemResult, ServiceListResult

#
# Service
#


class ServiceConfig:
    """Service Configuration."""

    # Common configuration for all Services
    service_id = None
    permission_policy_cls = BasePermissionPolicy
    result_item_cls = ServiceItemResult
    result_list_cls = ServiceListResult


#
# Class/Mixins
#


def _make_cls(cls, attrs):
    """Make the custom config class."""
    return type(
        f"Custom{cls.__name__}",
        (cls,),
        attrs,
    )


class ConfiguratorMixin:
    """Shared customization for requests service config."""

    @classmethod
    def build(cls, app):
        """Build the config object."""
        return type(f"Custom{cls.__name__}", (cls,), {"_app": app})()


class SearchOptionsMixin:
    """Customization of search options."""

    @classmethod
    def customize(cls, opts):
        """Customize the search options."""
        attrs = {}
        if opts.facets:
            attrs["facets"] = opts.facets
        if opts.sort_options:
            attrs["sort_options"] = opts.sort_options
            attrs["sort_default"] = opts.sort_default
            attrs["sort_default_no_query"] = opts.sort_default_no_query
        if opts.query_parser_cls:
            attrs["query_parser_cls"] = opts.query_parser_cls
        return _make_cls(cls, attrs) if attrs else cls


class FromConfig:
    """Data descriptor to connect config with application configuration.

    See https://docs.python.org/3/howto/descriptor.html .

    .. code-block:: python

        # service/config.py
        class ServiceConfig:
            foo = FromConfig("FOO", default=1)

        # config.py
        FOO = 2

        # ext.py
        c = ServiceConfig.build(app)
        c.foo  # 2
    """

    def __init__(self, config_key, default=None, import_string=False):
        """Constructor for data descriptor."""
        self.config_key = config_key
        self.default = default
        self.import_string = import_string

    def __get__(self, obj, objtype=None):
        """Return value that was grafted on obj (descriptor protocol)."""
        if self.import_string:
            return load_or_import_from_config(
                app=obj._app, key=self.config_key, default=self.default
            )
        else:
            return obj._app.config.get(self.config_key, self.default)

    def __set_name__(self, owner, name):
        """Store name of grafted field (descriptor protocol)."""
        # If we want to allow setting it we can implement this.
        pass

    def __set__(self, obj, value):
        """Set value on grafted_field of obj (descriptor protocol)."""
        # If we want to allow setting it we can implement this.
        pass


#
# Search
#


class OptionsSelector:
    """Generic helper to select and validate facet/sort options."""

    def __init__(self, available_options, selected_options):
        """Initialize selector."""
        # Ensure all selected options are availabe.
        for o in selected_options:
            assert o in available_options, f"Selected option '{o}' is undefined."

        self.available_options = available_options
        self.selected_options = selected_options

    def __iter__(self):
        """Iterate over options to produce RSK options."""
        for o in self.selected_options:
            yield self.map_option(o, self.available_options[o])

    def map_option(self, key, option):
        """Map an option."""
        # This interface is used in Invenio-App-RDM.
        return (key, option)


class SortOptionsSelector(OptionsSelector):
    """Sort options for the search configuration."""

    def __init__(
        self, available_options, selected_options, default=None, default_no_query=None
    ):
        """Initialize sort options."""
        super().__init__(available_options, selected_options)

        self.default = selected_options[0] if default is None else default
        self.default_no_query = (
            selected_options[1] if default_no_query is None else default_no_query
        )

        assert (
            self.default in self.available_options
        ), f"Default sort with query {self.default} is undefined."
        assert (
            self.default_no_query in self.available_options
        ), f"Default sort without query {self.default_no_query} is undefined."


class SearchConfig:
    """Search endpoint configuration."""

    def __init__(self, config, sort=None, facets=None):
        """Initialize search config."""
        config = config or {}
        self._sort = []
        self._facets = []
        self._query_parser_cls = None

        if "sort" in config:
            self._sort = SortOptionsSelector(
                sort,
                config["sort"],
                default=config.get("sort_default"),
                default_no_query=config.get("sort_default_no_query"),
            )

        if "facets" in config:
            self._facets = OptionsSelector(facets, config.get("facets"))

        if "query_parser_cls" in config:
            self._query_parser_cls = config["query_parser_cls"]

    @property
    def sort_options(self):
        """Get sort options for search."""
        return {k: v for (k, v) in self._sort}

    @property
    def sort_default(self):
        """Get default sort method for search."""
        return self._sort.default if self._sort else None

    @property
    def sort_default_no_query(self):
        """Get default sort method without query for search."""
        return self._sort.default_no_query if self._sort else None

    @property
    def facets(self):
        """Get facets for search."""
        return {k: v["facet"] for (k, v) in self._facets}

    @property
    def query_parser_cls(self):
        """Get query parser class for search."""
        return self._query_parser_cls


class FromConfigSearchOptions:
    """Data descriptor for search options configuration."""

    def __init__(
        self, config_key, sort_key, facet_key, default=None, search_option_cls=None
    ):
        """Constructor for data descriptor."""
        self.config_key = config_key
        self.sort_key = sort_key
        self.facet_key = facet_key
        self.default = default or {}
        self.search_option_cls = search_option_cls

    def __get__(self, obj, objtype=None):
        """Return value that was grafted on obj (descriptor protocol)."""
        search_opts = obj._app.config.get(self.config_key, self.default)
        sort_opts = obj._app.config.get(self.sort_key)
        facet_opts = obj._app.config.get(self.facet_key)

        search_config = SearchConfig(
            search_opts,
            sort=sort_opts,
            facets=facet_opts,
        )

        return self.search_option_cls.customize(search_config)
