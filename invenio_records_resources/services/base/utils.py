# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Utils."""


def get_search_params(config, params):
    """Distinguish search parameters."""
    page = params.get("page", 1)
    size = params.get(
        "size",
        config.search.pagination_options.get("default_results_per_page"),
    )

    _search_cls = config.search

    _sort_name = (
        params.get("sort")
        if params.get("sort") in _search_cls.sort_options
        else _search_cls.sort_default
    )
    _sort_direction_name = (
        params.get("sort_direction")
        if params.get("sort_direction") in _search_cls.sort_direction_options
        else _search_cls.sort_direction_default
    )

    sort = _search_cls.sort_options.get(_sort_name)
    sort_direction = _search_cls.sort_direction_options.get(_sort_direction_name)

    query_params = params.get("q", "")

    return {
        "page": page,
        "size": size,
        "sort": sort.get("fields"),
        "sort_direction": sort_direction.get("fn"),
        "q": query_params,
    }
