# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service utils tests."""

from sqlalchemy import asc, desc

from invenio_records_resources.services.base.utils import map_search_params


class MockSearchOptions:
    """Mock module search options."""

    sort_direction_default = "desc"
    sort_direction_options = {
        "asc": dict(
            title="Ascending",
            fn=asc,
        ),
        "desc": dict(
            title="Descending",
            fn=desc,
        ),
    }

    sort_default = "option2"
    sort_options = {
        "option1": dict(
            title="Option1",
            fields=["option1"],
        ),
        "option2": dict(
            title="Option2",
            fields=["option2"],
        ),
    }
    pagination_options = {
        "default_results_per_page": 25,
    }


def test_map_search_params(app):
    """Test mapping search params utility."""
    # using given params
    params = {
        "page": 2,
        "size": 2,
        "sort": "option1",
        "sort_direction": "asc",
        "q": "query",
    }
    search_params = map_search_params(MockSearchOptions, params)

    assert search_params.get("page") == 2
    assert search_params.get("size") == 2
    assert search_params.get("sort") == ["option1"]
    assert search_params.get("sort_direction") == asc
    assert search_params.get("q") == "query"

    # using default params
    params = {"sort": "option55", "sort_direction": "some direction"}
    search_params = map_search_params(MockSearchOptions, params)

    assert search_params.get("page") == 1
    assert search_params.get("size") == 25
    assert search_params.get("sort") == ["option2"]
    assert search_params.get("sort_direction") == desc
    assert search_params.get("q") == ""
