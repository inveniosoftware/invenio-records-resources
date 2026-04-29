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


class DateBoundedSearchOptions(SearchOptions):
    """Search options with hard_bounds."""

    facets = {
        "publication_date": DateFacet(
            field="metadata.publication_date_range",
            label="Publication year",
            interval="year",
            separator="..",
            hard_bounds={"min": "2019", "max": "now/y"},
        )
    }


class DateDirectFilterSearchOptions(SearchOptions):
    """Search options with post_filter=False."""

    facets = {
        "publication_date": DateFacet(
            field="metadata.publication_date_range",
            label="Publication year",
            interval="year",
            separator="..",
            post_filter=False,
        )
    }


class DateServiceConfig(ServiceConfig):
    """Service config for date facet tests."""

    search = DateSearchOptions


class DateBoundedServiceConfig(ServiceConfig):
    """Service config with hard_bounds."""

    search = DateBoundedSearchOptions


class DateDirectFilterServiceConfig(ServiceConfig):
    """Service config with post_filter=False."""

    search = DateDirectFilterSearchOptions


@pytest.fixture()
def date_service(appctx):
    """Service instance for date facet tests."""
    return RecordService(DateServiceConfig)


@pytest.fixture()
def date_bounded_service(appctx):
    """Service instance with hard_bounds."""
    return RecordService(DateBoundedServiceConfig)


@pytest.fixture()
def date_direct_filter_service(appctx):
    """Service instance with post_filter=False."""
    return RecordService(DateDirectFilterServiceConfig)


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


@pytest.fixture()
def date_records_wide(app, date_service, identity_simple, search_clear):
    """Records spanning a wide date range for bounds testing."""
    items = []
    for year, title in [(1700, "old"), (2019, "recent-1"), (2020, "recent-2")]:
        items.append(
            date_service.create(
                identity_simple,
                {
                    "metadata": {
                        "title": title,
                        "publication_date_range": {
                            "gte": f"{year}-01-01",
                            "lte": f"{year}-12-31",
                        },
                    }
                },
            )
        )
    Record.index.refresh()
    return items


def test_hard_bounds_clips_histogram(
    app, date_bounded_service, identity_simple, date_records_wide
):
    """hard_bounds clips histogram buckets to the configured range."""
    res = date_bounded_service.search(identity_simple)
    bucket_keys = [b["key"] for b in res.aggregations["publication_date"]["buckets"]]
    # 1700 should be clipped by hard_bounds min=2019
    assert "1700" not in bucket_keys
    assert "2019" in bucket_keys
    assert "2020" in bucket_keys
    # All 3 records still returned (hard_bounds only affects aggregation)
    assert 3 == len(res)


def test_hard_bounds_expand_outside_filter(
    app, date_bounded_service, identity_simple, date_records_wide
):
    """Filtering outside hard_bounds expands bounds to show filter range."""
    res = date_bounded_service.search(
        identity_simple, facets={"publication_date": ["1600..1800"]}
    )
    bucket_keys = [b["key"] for b in res.aggregations["publication_date"]["buckets"]]
    # Bounds expanded to filter range, 1700 bucket should appear
    assert "1700" in bucket_keys
    # Only the 1700 record matches the filter
    assert 1 == len(res)


def test_post_filter_false_affects_aggregations(
    app, date_direct_filter_service, identity_simple, date_records_wide
):
    """post_filter=False makes aggregations reflect filtered results."""
    res = date_direct_filter_service.search(
        identity_simple, facets={"publication_date": ["2020"]}
    )
    buckets = res.aggregations["publication_date"]["buckets"]
    non_zero = [b for b in buckets if b["doc_count"] > 0]
    # Only 2020 bucket should have counts (direct filter affects aggregation)
    assert all(b["key"] == "2020" for b in non_zero)
    assert 1 == len(res)


def test_post_filter_true_preserves_aggregations(
    app, date_service, identity_simple, date_records_wide
):
    """Default post_filter=True preserves aggregation counts from full result set."""
    res = date_service.search(identity_simple, facets={"publication_date": ["2020"]})
    buckets = {
        b["key"]: b["doc_count"]
        for b in res.aggregations["publication_date"]["buckets"]
    }
    # 1700 and 2019 buckets still have counts (post_filter doesn't affect aggs)
    assert buckets.get("1700", 0) == 1
    assert buckets.get("2019", 0) == 1
    assert buckets.get("2020", 0) == 1
    # But only 2020 records returned
    assert 1 == len(res)


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
        "start_raw": "2020",
        "end_raw": "2020",
        "start_inclusive": True,
        "end_inclusive": True,
    } == normalized
    normalized = facet._normalize_value("..2020")
    assert {
        "start": None,
        "end": "2020-12-31",
        "start_raw": None,
        "end_raw": "2020",
        "start_inclusive": True,
        "end_inclusive": True,
    } == normalized

    normalized = facet._normalize_value("2019..")
    assert {
        "start": "2019-01-01",
        "end": None,
        "start_raw": "2019",
        "end_raw": None,
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


def test_date_facet_range_query_uses_date_math():
    """Range queries use ||/y, ||/M, ||/d rounding so exclusive bounds work."""
    facet = DateFacet(field="date", label="Date")

    # Inclusive year: gte rounds down to start of year
    q = facet._build_range_query("[2020..2025]").to_dict()["range"]["date"]
    assert q["gte"] == "2020||/y"
    assert q["lte"] == "2025||/y"

    # Exclusive year: gt rounds up to next year, lt rounds down to previous
    q = facet._build_range_query("(2020..2025)").to_dict()["range"]["date"]
    assert q["gt"] == "2020||/y"
    assert q["lt"] == "2025||/y"

    # Mixed precision
    q = facet._build_range_query("2020-03..2020-03-15").to_dict()["range"]["date"]
    assert q["gte"] == "2020-03||/M"
    assert q["lte"] == "2020-03-15||/d"


def test_date_facet_effective_date_respects_inclusivity():
    """Effective dates shift by one period for exclusive bounds."""
    facet = DateFacet(field="date", label="Date")

    # (1970..]: exclusive year start → effective start is 1971-01-01
    r = facet._normalize_value("(1970..]")
    assert facet._effective_date(r, is_start=True) == "1971-01-01"

    # [1970..]: inclusive year start → effective start is 1970-01-01
    r = facet._normalize_value("[1970..]")
    assert facet._effective_date(r, is_start=True) == "1970-01-01"

    # [..1970): exclusive year end → effective end is 1969-12-31
    r = facet._normalize_value("[..1970)")
    assert facet._effective_date(r, is_start=False) == "1969-12-31"

    # Month-precision exclusive end (2020-03 excluded → end is Feb 2020)
    r = facet._normalize_value("[..2020-03)")
    assert facet._effective_date(r, is_start=False) == "2020-02-29"

    # Day-precision exclusive start (2020-03-15 excluded → starts 2020-03-16)
    r = facet._normalize_value("(2020-03-15..]")
    assert facet._effective_date(r, is_start=True) == "2020-03-16"


def test_date_facet_outside_bounds_with_exclusive():
    """Exclusive bounds at the edge of hard_bounds are NOT outside."""
    bounds = {"min": "1970", "max": "now/y"}

    def is_outside(filter_value):
        f = DateFacet(field="date", label="Date", hard_bounds=bounds.copy())
        f.prepare_aggregation([filter_value])
        return f._is_outside_bounds(f._normalize_value(filter_value))

    # (1969..]: exclusive of 1969 → effective start 1970 → at boundary, NOT outside
    assert not is_outside("(1969..]")
    # [1969..]: inclusive → effective start 1969 → before boundary, outside
    assert is_outside("[1969..]")
    # [1970..]: at boundary, NOT outside
    assert not is_outside("[1970..]")
    # (1968..]: exclusive of 1968 → effective start 1969 → still outside
    assert is_outside("(1968..]")


def test_date_facet_post_filter():
    """post_filter defaults to True and can be overridden per-instance."""
    facet = DateFacet(field="date", label="Date")
    assert facet.post_filter is True

    facet_direct = DateFacet(field="date", label="Date", post_filter=False)
    assert facet_direct.post_filter is False

    # Other instances are unaffected
    assert facet.post_filter is True


def test_date_facet_hard_bounds_aggregation():
    """hard_bounds is passed to the aggregation when configured."""
    facet = DateFacet(
        field="date",
        label="Date",
        hard_bounds={"min": "1800", "max": "now/y"},
    )
    agg = facet.get_aggregation()
    assert agg.to_dict()["date_histogram"]["hard_bounds"] == {
        "min": "1800",
        "max": "now/y",
    }

    # Without hard_bounds, no hard_bounds key
    facet_no_bounds = DateFacet(field="date", label="Date")
    agg = facet_no_bounds.get_aggregation()
    assert "hard_bounds" not in agg.to_dict()["date_histogram"]


def test_date_facet_effective_bounds():
    """Effective bounds depend on match_filter_bounds and the active filter."""
    bounds = {"min": "1970", "max": "now/y"}

    def make_facet(filter_value, match=False):
        f = DateFacet(
            field="date",
            label="Date",
            hard_bounds=bounds.copy(),
            match_filter_bounds=match,
        )
        f.prepare_aggregation([filter_value])
        return f._effective_bounds()

    # No filter — configured bounds preserved
    for match in (False, True):
        facet = DateFacet(
            field="date",
            label="Date",
            hard_bounds=bounds.copy(),
            match_filter_bounds=match,
        )
        assert facet._effective_bounds() == bounds

    # Default (match_filter_bounds=False): inside-bound filter keeps configured bounds
    assert make_facet("2000..2025") == {"min": "1970", "max": "now/y"}
    # Default: outside-bound filter replaces with filter range
    assert make_facet("1500..1700") == {"min": "1500", "max": "1700"}
    assert make_facet("1500..2020") == {"min": "1500", "max": "2020"}

    # match_filter_bounds=True: filter range always used
    assert make_facet("2000..2025", match=True) == {"min": "2000", "max": "2025"}
    assert make_facet("1500..1700", match=True) == {"min": "1500", "max": "1700"}
    assert make_facet("1500..", match=True) == {"min": "1500"}

    # No mutation of original _hard_bounds
    facet = DateFacet(field="date", label="Date", hard_bounds=bounds.copy())
    facet.prepare_aggregation(["1500..1700"])
    facet._effective_bounds()
    assert facet._hard_bounds == bounds


def test_date_facet_format_bound():
    """Bounds are formatted to match the aggregation format."""
    facet_y = DateFacet(field="date", label="Date", format="yyyy")
    assert facet_y._format_bound("1500-01-01") == "1500"
    assert facet_y._format_bound("2020-06-15") == "2020"

    facet_ym = DateFacet(field="date", label="Date", format="yyyy-MM")
    assert facet_ym._format_bound("2020-06-15") == "2020-06"

    facet_ymd = DateFacet(field="date", label="Date", format="yyyy-MM-dd")
    assert facet_ymd._format_bound("2020-06-15") == "2020-06-15"

    # Effective bounds respect format
    facet = DateFacet(
        field="date",
        label="Date",
        format="yyyy",
        hard_bounds={"min": "1800", "max": "now/y"},
    )
    facet.prepare_aggregation(["1000..1800"])
    assert facet._effective_bounds() == {"min": "1000", "max": "1800"}
