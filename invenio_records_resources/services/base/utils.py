# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Services utils."""


def map_search_params(service_search_config, params):
    """Map search params to a dictionary, useful for searches in DB.

    :params service_search_config: search configuration class
    :params params: the user query params for the search
    :returns dict: a dict in this shape:
        {
            "page": int,
            "size": int,
            "sort": list of fields for sorting,
            "sort_direction": ordering function,
            "q": string,
        }
    """
    _config = service_search_config

    page = params.get("page", 1)
    size = params.get(
        "size",
        _config.pagination_options.get("default_results_per_page", 25),
    )

    _sort_name = (
        params["sort"]
        if params.get("sort") in _config.sort_options
        else _config.sort_default
    )
    _sort_direction_name = (
        params["sort_direction"]
        if params.get("sort_direction") in _config.sort_direction_options
        else _config.sort_direction_default
    )

    sort = _config.sort_options.get(_sort_name, {})
    sort_direction = _config.sort_direction_options.get(_sort_direction_name, {})

    query_params = params.get("q", "")

    return {
        "page": page,
        "size": size,
        "sort": sort.get("fields"),
        "sort_direction": sort_direction.get("fn"),
        "q": query_params,
    }
