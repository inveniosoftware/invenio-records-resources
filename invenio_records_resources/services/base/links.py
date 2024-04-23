# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Flask-Resources is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utility for rendering URI template links."""

import operator
from copy import deepcopy

from flask import current_app
from invenio_records.dictutils import dict_lookup
from uritemplate import URITemplate
from werkzeug.datastructures import MultiDict


def _unpack_dict(data):
    """Unpack lists inside a dict.

    For instance this dictionary:

    .. code-block:: python

        {
            "type": ["A", "B"],
            "sort": "newest",
        }

    Is expanded to:

    .. code-block:: python

        [
            ("sort", "newest"),
            ("type", "A"),
            ("type", "B"),
        ]
    """
    for key, value in sorted(data.items()):
        if isinstance(value, list):
            for v in value:
                yield key, v
        else:
            yield key, value


def preprocess_vars(vars):
    """Preprocess template variables before expansion."""
    for k, v in vars.items():
        if isinstance(v, MultiDict):
            vars[k] = list(sorted(v.items(multi=True)))
        elif isinstance(v, dict):
            # Note, we unpack dicts with list values at this level, because
            # there are no meaningful templates that can make use of them
            # (basically the lists just becomes URL encoded python objects)
            vars[k] = list(_unpack_dict(v))
    return vars


class LinksTemplate:
    """Templates for generating links for an object."""

    def __init__(self, links=None, context=None):
        """Initialize the link templates."""
        self._links = links or {}
        self._context = context or {}

    @property
    def context(self):
        """Get the context for the links."""
        ctx = {}
        if current_app:
            ctx.update(
                {
                    "ui": current_app.config.get("SITE_UI_URL", ""),
                    "api": current_app.config.get("SITE_API_URL", "/api"),
                }
            )
        ctx.update(self._context)
        return ctx

    def expand(self, identity, obj):
        """Expand all the link templates."""
        links = {}
        ctx = deepcopy(self.context)
        # pass identity to context
        ctx["identity"] = identity
        for key, link in self._links.items():
            if link.should_render(obj, ctx):
                links[key] = link.expand(obj, ctx)
        return links


class Link:
    """Utility class for keeping track of and resolve links."""

    def __init__(self, uritemplate, when=None, vars=None):
        """Constructor."""
        self._uritemplate = URITemplate(uritemplate)
        self._when_func = when
        self._vars_func = vars

    def should_render(self, obj, ctx):
        """Determine if the link should be rendered."""
        if self._when_func:
            return bool(self._when_func(obj, ctx))
        return True

    @staticmethod
    def vars(obj, vars):
        """Subclasses can overwrite this method."""
        pass

    def expand(self, obj, context):
        """Expand the URI Template."""
        vars = {}
        vars.update(deepcopy(context))
        self.vars(obj, vars)
        if self._vars_func:
            self._vars_func(obj, vars)
        vars = preprocess_vars(vars)
        return self._uritemplate.expand(**vars)


class ConditionalLink:
    """Conditional link."""

    def __init__(self, cond=None, if_=None, else_=None):
        """Constructor."""
        self._condition = cond
        self._if_link = if_
        self._else_link = else_

    def should_render(self, obj, ctx):
        """Determine if the link should be rendered."""
        if self._condition(obj, ctx):
            return self._if_link.should_render(obj, ctx)
        else:
            return self._else_link.should_render(obj, ctx)

    def expand(self, obj, ctx):
        """Determine if the link should be rendered."""
        if self._condition(obj, ctx):
            return self._if_link.expand(obj, ctx)
        else:
            return self._else_link.expand(obj, ctx)


class NestedLinks:
    """Base class for generating nested links."""

    def __init__(
        self,
        links,
        key=None,
        load_key=None,
        dump_key=None,
        context_func=None,
    ):
        """Initialize NestedLinkGenerator."""
        self.links = links
        self.load_key = load_key or key
        self.dump_key = dump_key or key
        assert self.load_key and self.dump_key
        self.context_func = context_func

    def context(self, identity, record, key, value):
        """Get the context for the links."""
        if not self.context_func:
            return {}
        return self.context_func(identity, record, key, value)

    def expand(self, identity, record, data):
        """Update data with links in each object inside the dictionary."""
        try:
            record_data = operator.attrgetter(self.load_key)(record)
        except AttributeError:
            return
        try:
            output_data = dict_lookup(data, self.dump_key)
        except KeyError:
            return

        if isinstance(record_data, (tuple, list)):
            items_iter = enumerate(record_data)
        elif isinstance(record_data, dict):
            items_iter = record_data.items()
        else:
            return

        for key, value in items_iter:
            context = self.context(identity, record, key, value)
            links = LinksTemplate(self.links, context=context).expand(identity, value)
            output_data[key]["links"] = links
