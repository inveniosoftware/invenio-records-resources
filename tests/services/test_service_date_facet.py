# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Date facets tests."""

import pytest

from invenio_records_resources.services import RecordService, SearchOptions
from invenio_records_resources.services.records.facets import DateFacet
from tests.mock_module.api import Record
from tests.mock_module.config import ServiceConfig


class DateSearchOptions(SearchOptions):
    """Search options for date facet tests."""

    facets = {
        "publication_date": DateFacet(
            field="metadata.publication_date_range",
            label="Publication year",
            interval="year",
            separator="..",
        )
    }


class DateServiceConfig(ServiceConfig):
    """Service config for date facet tests."""

    search = DateSearchOptions


@pytest.fixture()
def date_service(appctx):
    """Service instance for date facet tests."""
    return RecordService(DateServiceConfig)


@pytest.fixture()
def date_records(app, date_service, identity_simple, search_clear):
    """Input data for date facet tests."""
    items = []
    items.append(
        date_service.create(
            identity_simple,
            {
                "metadata": {
                    "title": "2019",
                    "publication_date_range": {
                        "gte": "2019-01-01",
                        "lte": "2019-12-31",
                    },
                }
            },
        )
    )
    items.append(
        date_service.create(
            identity_simple,
            {
                "metadata": {
                    "title": "2020",
                    "publication_date_range": {
                        "gte": "2020-01-01",
                        "lte": "2020-12-31",
                    },
                }
            },
        )
    )
    items.append(
        date_service.create(
            identity_simple,
            {
                "metadata": {
                    "title": "2020-05",
                    "publication_date_range": {
                        "gte": "2020-05-01",
                        "lte": "2020-05-31",
                    },
                }
            },
        )
    )
    Record.index.refresh()
    return items


def test_date_facets(app, date_service, identity_simple, date_records):
    res = date_service.search(identity_simple)
    expected_aggs = {
        "publication_date": {
            "buckets": [
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "2019",
                    "label": "2019",
                },
                {
                    "doc_count": 2,
                    "is_selected": False,
                    "key": "2020",
                    "label": "2020",
                },
            ],
            "label": "Publication year",
        },
    }

    assert expected_aggs == res.aggregations


def test_date_facets_filtering(app, date_service, identity_simple, date_records):
    res = date_service.search(identity_simple, facets={"publication_date": ["2020"]})
    expected_aggs = {
        "publication_date": {
            "buckets": [
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "2019",
                    "label": "2019",
                },
                {
                    "doc_count": 2,
                    "is_selected": True,
                    "key": "2020",
                    "label": "2020",
                },
            ],
            "label": "Publication year",
        },
    }

    assert expected_aggs == res.aggregations
    assert 2 == len(res)
    assert set(["2020", "2020-05"]) == set([h["metadata"]["title"] for h in res])


def test_date_facets_range_filtering(app, date_service, identity_simple, date_records):
    res = date_service.search(
        identity_simple, facets={"publication_date": ["2019..2020"]}
    )
    expected_aggs = {
        "publication_date": {
            "buckets": [
                {
                    "doc_count": 1,
                    "is_selected": True,
                    "key": "2019",
                    "label": "2019",
                },
                {
                    "doc_count": 2,
                    "is_selected": True,
                    "key": "2020",
                    "label": "2020",
                },
            ],
            "label": "Publication year",
        },
    }

    assert expected_aggs == res.aggregations
    assert 3 == len(res)


def test_date_facets_invalid_filter(app, date_service, identity_simple, date_records):
    res = date_service.search(
        identity_simple, facets={"publication_date": ["not-a-date"]}
    )
    expected_aggs = {
        "publication_date": {
            "buckets": [
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "2019",
                    "label": "2019",
                },
                {
                    "doc_count": 2,
                    "is_selected": False,
                    "key": "2020",
                    "label": "2020",
                },
            ],
            "label": "Publication year",
        },
    }

    assert expected_aggs == res.aggregations
    assert 3 == len(res)


def test_date_facet_normalize_value():
    facet = DateFacet(
        field="metadata.publication_date_range",
        label="Publication year",
        interval="year",
        separator="..",
    )

    normalized = facet._normalize_value("2020")
    assert {
        "start": "2020-01-01",
        "end": "2020-12-31",
        "start_inclusive": True,
        "end_inclusive": True,
    } == normalized
    normalized = facet._normalize_value("..2020")
    assert {
        "start": None,
        "end": "2020-12-31",
        "start_inclusive": True,
        "end_inclusive": True,
    } == normalized

    normalized = facet._normalize_value("2019..")
    assert {
        "start": "2019-01-01",
        "end": None,
        "start_inclusive": True,
        "end_inclusive": True,
    } == normalized

    assert facet._normalize_value("not-a-date") is None


def test_date_facet_normalize_date():
    facet = DateFacet(
        field="metadata.publication_date_range",
        label="Publication year",
        interval="year",
        separator="..",
    )

    assert "2020-01-01" == facet._normalize_date("2020", is_start=True)
    assert "2020-12-31" == facet._normalize_date("2020", is_start=False)
    assert "2020-02-01" == facet._normalize_date("2020-02", is_start=True)
    assert "2020-02-29" == facet._normalize_date("2020-02", is_start=False)


def test_date_facet_last_day_of_month():
    assert 29 == DateFacet._last_day_of_month(2020, 2)
    assert 28 == DateFacet._last_day_of_month(2019, 2)
    assert 31 == DateFacet._last_day_of_month(2021, 12)
