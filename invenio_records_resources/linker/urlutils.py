# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

from flask import current_app


def base_url(
        scheme="https", host=None, path="/", querystring="", api=False):
    """Creates the URL for API and UI endpoints."""
    assert path.startswith("/")
    path = f"/api{path}" if api else path
    host = host or current_app.config['SERVER_HOSTNAME']
    return f"{scheme}://{host}{path}{querystring}"


def api_route(route):
    """Prepends the route with '/api'."""
    assert route.startswith("/")
    return f"/api{route}"
