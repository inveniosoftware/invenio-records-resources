# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Flask-Resources is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utility for rendering URI template links."""

from copy import deepcopy

from flask import current_app
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

    def __init__(self, links, context=None):
        """Initialize the link templates."""
        self._links = links
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
