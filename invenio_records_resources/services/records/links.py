# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2025 Northwestern University.
#
# Flask-Resources is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utility for rendering URI template links."""

from ..base import EndpointLink, Link


class RecordLink(Link):
    """Deprecated shortcut for writing record links."""

    @staticmethod
    def vars(record, vars):
        """Variables for the URI template."""
        # Some records don't have record.pid.pid_value yet (e.g. drafts)
        pid_value = getattr(record.pid, "pid_value", None)
        if pid_value:
            vars.update({"id": record.pid.pid_value})


class RecordEndpointLink(EndpointLink):
    """Rendering of a record link with specific vars expansion."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super().__init__(*args, **kwargs)
        # Conveniently add pid_value to params
        if "pid_value" not in self._params:
            self._params.append("pid_value")

    @staticmethod
    def vars(record, vars):
        """Variables for the endpoint expansion."""
        # Some records don't have record.pid.pid_value yet (e.g. drafts)
        pid_value = getattr(record.pid, "pid_value", None)
        if pid_value:
            vars.update({"pid_value": pid_value})


def pagination_links(tpl):
    """Create pagination links (prev/self/next) from the same template."""
    return {
        "prev": Link(
            tpl,
            when=lambda pagination, ctx: pagination.has_prev,
            vars=lambda pagination, vars: vars["args"].update(
                {"page": pagination.prev_page.page}
            ),
        ),
        "self": Link(tpl),
        "next": Link(
            tpl,
            when=lambda pagination, ctx: pagination.has_next,
            vars=lambda pagination, vars: vars["args"].update(
                {"page": pagination.next_page.page}
            ),
        ),
    }


def pagination_endpoint_links(endpoint, params=None):
    """Create pagination links (prev/self/next) from the same endpoint."""
    return {
        "prev": EndpointLink(
            endpoint,
            when=lambda pagination, ctx: pagination.has_prev,
            vars=lambda pagination, vars: vars["args"].update(
                {"page": pagination.prev_page.page}
            ),
            params=params,
        ),
        "self": EndpointLink(endpoint, params=params),
        "next": EndpointLink(
            endpoint,
            when=lambda pagination, ctx: pagination.has_next,
            vars=lambda pagination, vars: vars["args"].update(
                {"page": pagination.next_page.page}
            ),
            params=params,
        ),
    }
