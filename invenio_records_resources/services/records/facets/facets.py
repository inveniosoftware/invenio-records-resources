# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2026 CERN.
# Copyright (C) 2023 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets types defined."""

import re
from datetime import date, timedelta

from dateutil.parser import isoparse
from invenio_search.engine import dsl


class Facet(dsl.Facet):
    """Base facet with filtering behavior defaults.

    Subclasses can override ``post_filter`` to control whether their filter is
    applied as a post_filter (preserves aggregation counts from the full result
    set) or as a direct query filter (aggregations reflect filtered results).

    ``post_filter`` can be set as a class attribute, passed to the constructor,
    or set on an instance after construction.
    """

    post_filter = True

    def __init__(self, post_filter=None, **kwargs):
        """Constructor."""
        if post_filter is not None:
            self.post_filter = post_filter
        super().__init__(**kwargs)

    def prepare_aggregation(self, filter_values):
        """Prepare the aggregation based on active filter values. No-op by default."""
        pass


class LabelledFacetMixin:
    """Mixin class for overwriting the default get_values() method."""

    def __init__(self, label=None, value_labels=None, **kwargs):
        """Initialize class."""
        self._label = label or ""
        self._value_labels = value_labels
        super().__init__(**kwargs)

    def get_value(self, bucket):
        """Get key value for a bucket."""
        return getattr(bucket, "key_as_string", bucket.key)

    def get_label_mapping(self, buckets):
        """Overwrite this method to provide custom labelling."""
        keys = [self.get_value(b) for b in buckets]
        value_labels = self._value_labels or {}

        if callable(value_labels):
            return value_labels(keys)
        else:
            return {k: value_labels.get(k, k) for k in keys}

    def get_values(self, data, filter_values):
        """Get an unlabelled version of the bucket."""
        out = []
        for bucket in data.buckets:
            key = self.get_value(bucket)
            out.append(
                {
                    "key": key,
                    "doc_count": self.get_metric(bucket),
                    "is_selected": self.is_filtered(key, filter_values),
                }
            )

        return {"buckets": out}

    def get_labelled_values(self, data, filter_values):
        """Get a labelled version of a bucket."""
        out = []
        # We get the labels first, so that we can efficiently query a resource
        # for all keys in one go, vs querying one by one if needed.
        label_map = self.get_label_mapping(data.buckets)
        for bucket in data.buckets:
            key = self.get_value(bucket)
            out.append(
                {
                    "key": key,
                    "doc_count": self.get_metric(bucket),
                    "label": label_map[key],
                    "is_selected": self.is_filtered(key, filter_values),
                }
            )
        return {"buckets": out, "label": str(self._label)}


class TermsFacet(LabelledFacetMixin, Facet, dsl.TermsFacet):
    """Terms facet.

    .. code-block:: python

        facets = {
            'is_published': TermsFacet(
                field='is_published',
                label=_('Status'),
                value_labels={0: _('Unpublished'), 1: _('Published')}
            ),
            'languages': TermsFacet(
                field='metadata.languages.id',
                label=_('Languages'),
                value_labels=lambda keys: {k: k} }
            )
        }
    """

    # Note, LabelledFacetMixin must be first class instantiated. This ensures
    # that we overwrite the Facet.get_values() method in the Facet base class.


class NestedTermsFacet(TermsFacet):
    """A hierarchical terms facet.

    .. code-block:: python

        facets = {
            'resource_type': NestedTermsFacet(
                field='metadata.resource_type.type',
                subfield='metadata.resource_type.subtype',
                splitchar='::',
                label=_('Resource types'),
                value_labels=VocabularyL10NLabels(current_service)
            )
        }
    """

    def __init__(self, field=None, subfield=None, splitchar="::", **kwargs):
        """Initialize the nested terms facet."""
        self._field = field
        self._subfield = subfield
        self._splitchar = splitchar
        super().__init__(**kwargs)

    def get_aggregation(self):
        """Get the aggregation and subaggregation."""
        return dsl.A(
            "terms",
            field=self._field,
            aggs={"inner": dsl.A("terms", field=self._subfield)},
        )

    def _parse_values(self, filter_values):
        """Builds a hierarchical structure of values used for filtering.

        Takes as input a list of filter values like:

        .. code-block:: python

            [
                'publication',
                'publication::book',
                'publication::journal',
                'dataset'
            ]

        and creates a datastructure for quering:

        .. code-block:: python

            {
                'publication': ['book', 'journal'],
                'dataset': []
            }

        """
        parsed_values = {}

        for value in filter_values:
            # Get the aggregation type
            field_value, *subfield_values = value.split(self._splitchar)

            # If aggregation type is not present in field_values,
            # add them to dict with a empty list
            if field_value not in parsed_values:
                parsed_values[field_value] = []

            # If subfields are present, append the subfield aggregations to the
            # belonging aggregation type key
            if subfield_values:
                # We ignore invalid data.
                parsed_values[field_value].append(subfield_values[-1])

        return parsed_values

    def get_value_filter(self, parsed_value):
        """Return a filter for a single parsed value."""
        # Expects to get a value from the output of "_parse_values()"."
        field_value, subfield_values = parsed_value

        q = dsl.Q("term", **{self._field: field_value})
        if subfield_values:
            q &= dsl.Q("terms", **{self._subfield: subfield_values})
        return q

    def add_filter(self, filter_values):
        """Construct a filter query for the facet."""
        if not filter_values:
            return

        parsed_values = list(self._parse_values(filter_values).items())

        f = self.get_value_filter(parsed_values[0])
        for v in parsed_values[1:]:
            f |= self.get_value_filter(v)

        return f

    def get_values(self, data, filter_values, key_prefix=None):
        """Get an unlabelled version of the bucket."""
        out = []
        for bucket in data.buckets:
            key = full_key = self.get_value(bucket)
            if key_prefix:
                full_key = key_prefix + self._splitchar + full_key
            bucket_out = {
                "key": key,
                "doc_count": self.get_metric(bucket),
                "is_selected": self.is_filtered(full_key, filter_values),
            }
            if "inner" in bucket:
                bucket_out["inner"] = self.get_values(
                    bucket.inner, filter_values, key_prefix=full_key
                )
            out.append(bucket_out)
        return {"buckets": out}

    def get_labelled_values(
        self, data, filter_values, bucket_label=True, key_prefix=None
    ):
        """Get a labelled version of a bucket."""
        out = []
        # We get the labels first, so that we can efficiently query a resource
        # for all keys in one go, vs querying one by one if needed.
        label_map = self.get_label_mapping(data.buckets)
        for bucket in data.buckets:
            key = full_key = self.get_value(bucket)
            if key_prefix:
                full_key = key_prefix + self._splitchar + full_key
            bucket_out = {
                "key": key,
                "doc_count": self.get_metric(bucket),
                "label": label_map[key],
                "is_selected": self.is_filtered(full_key, filter_values),
            }
            if "inner" in bucket:
                bucket_out["inner"] = self.get_labelled_values(
                    bucket.inner, filter_values, bucket_label=False, key_prefix=full_key
                )
            out.append(bucket_out)
        ret_val = {"buckets": out}
        if bucket_label:
            ret_val["label"] = str(self._label)
        return ret_val


class CombinedTermsFacet(NestedTermsFacet):
    """
    Facet to mimic a nested aggregation without having to define a 'nested' field.

    This facet is needed to prevent the "crossed wires" problem of a regular
    NestedTermsFacet applied to documents with multiple 2-level objects. For example,
    and the motivating use case for this facet, a "subjects" field with the
    following mapping:

    .. code-block:: json

        "subjects": {
            "type": "object",
            "properties": {
                "scheme": {
                    "type": "keyword"
                },
                "subject": {
                    "type": "keyword"
                }
            }
        }

    will lead the document with the following subjects field:

    .. code-block:: json

        "subjects": [
            {"scheme": "SC1", "subject": "SU1"},
            {"scheme": "SC2", "subject": "SU2"}
        ]

    to be internally-indexed in the following manner:

    .. code-block:: json

        "subjects.scheme": ["SC1", "SC2"]
        "subjects.subject": ["SU1", "SU2"]

    . This indexing loses the original pairwise relationships. This causes searches
    and aggregations for scheme = SC1 and subject = SU2 to surface the above document
    when they shouldn't. This is the "crossed wires" problem that this Facet class
    resolves for aggregations without using "nested" types and searches (the classic
    solution to this problem).

    This facet requires the following indexed format:

    .. code-block:: json

        "<field>": ["<parent>", ...]
        // may have independent "<child>" entries
        "<combined field>": ["<parent><split char><child>", ..., "<child>"]

    The reasoning given for avoiding "nested" fields is to allow regular queries on
    those fields that would have had to be made "nested" (only nested queries can be
    done on those fields). This is a UX concern since end-users can make queries to
    metadata field directly and they wouldn't be able to anymore (without a lot more
    changes).

    Although this facet allows us to forego the need for a "nested" type field and
    nested queries to filter on that field, it *does* do extra work that is thrown away.
    See `get_aggregation` and `get_labelled_values`.

    This facet formats the result of the aggregation such that it looks like it was
    a nested aggregation.
    """

    def __init__(self, field, combined_field, parents, splitchar="::", **kwargs):
        """Constructor.

        :param field: top-level/parent field
        :type field: str
        :param combined_field: field containing combined terms
        :type combined_field: str
        :param groups: iterable of parent/top-level values
        :type groups: Iterable[str]
        :param splitchar: splitting/combining token, defaults to "::"
        :type splitchar: str, optional
        """
        self._field = field
        self._combined_field = combined_field
        self._parents = parents
        self._cached_parents = None
        self._splitchar = splitchar
        TermsFacet.__init__(self, **kwargs)

    def get_parents(self):
        """Return parents.

        We have to delay getting the parents since it may require an application
        context.
        """
        if not self._cached_parents:
            if callable(self._parents):
                self._cached_parents = self._parents()
            else:
                self._cached_parents = self._parents
        return self._cached_parents

    def get_aggregation(self):
        """Aggregate.

        This aggregation repeats ALL group subaggregation for each bucket generated
        by the top-level terms aggregation. This is to overcome the
        "irrelevant flooding" problem: when aggregating on a subfield, the top 10
        (by default) most frequent terms of that subfield are selected, but those
        terms may not be relevant to the parent because the parent-child relationship
        is lost when not using "nested". So to make sure only relevant terms are
        used to select the documents in the aggregation, we "include" (filter) for them.

        Only the subaggregation corresponding to the top-level group will be kept in
        get_labelled_values.
        """
        return dsl.A(
            {
                "terms": {
                    "field": self._field,
                    "aggs": {
                        f"inner_{parent}": {
                            "terms": {
                                "field": self._combined_field,
                                "include": f"{parent}{self._splitchar}.*",
                            },
                        }
                        for parent in self.get_parents()
                    },
                }
            }
        )

    def get_labelled_values(self, data, filter_values):
        """Get a labelled version of a bucket.

        :param data: Bucket data returned by document engine for a field
        :type data: dsl.response.aggs.FieldBucketData
        """

        def get_child_buckets(bucket, key):
            """Get lower-level/child buckets."""
            result = []

            # Ignore other subaggregations, and only retrieve inner_{key} one.
            # inner_{key} should always be present unless disconnect between
            # parents passed to generate subaggregations and parents actually present.
            # To not break in that case, we put a default empty list value.
            inner_data = getattr(bucket, f"inner_{key}", dsl.AttrDict({"buckets": []}))

            for inner_bucket in inner_data.buckets:
                # get raw key and appropriately formatted key
                key_raw_inner = self.get_value(inner_bucket)
                prefix = key + self._splitchar
                key_inner = key_raw_inner[len(prefix):]  # fmt: skip

                result.append(
                    {
                        "key": key_inner,
                        "doc_count": self.get_metric(inner_bucket),
                        "label": key_inner,
                        "is_selected": self.is_filtered(key_raw_inner, filter_values),
                    }
                )

            return result

        def get_parent_buckets(data):
            """Get top-level/group buckets.

            :param data: Bucket data returned by document engine for a field
            :type data: dsl.response.aggs.FieldBucketData
            :return: list of labelled buckets
            :rtype: List[dict]
            """
            label_map = self.get_label_mapping(data.buckets)
            result = []
            for bucket in data.buckets:
                key = self.get_value(bucket)
                result.append(
                    {
                        "key": key,
                        "doc_count": self.get_metric(bucket),
                        "label": label_map[key],
                        "is_selected": self.is_filtered(key, filter_values),
                        "inner": {"buckets": get_child_buckets(bucket, key)},
                    }
                )
            return result

        return {"buckets": get_parent_buckets(data), "label": str(self._label)}

    def get_value_filter(self, parsed_value):
        """Return a filter for a single parsed value."""
        # Expect to get a value from the output of `_parse_values()`
        field_value, subfield_values = parsed_value

        # recombine
        subfield_values = [
            f"{field_value}{self._splitchar}{subvalue}" for subvalue in subfield_values
        ]

        q = dsl.Q("term", **{self._field: field_value})
        if subfield_values:
            q &= dsl.Q("terms", **{self._combined_field: subfield_values})
        return q


class CFFacetMixin:
    """Mixin to abstract the custom fields path."""

    @classmethod
    def field(cls, field):
        """Format field with `custom_fields` prefix."""
        return f"custom_fields.{field}"


class CFTermsFacet(CFFacetMixin, TermsFacet):
    """Terms facet for custom fields.

    Works exactly as TermsFacet except that prepends the prefix `custom_fields`
    in the field definition.
    """

    def __init__(self, field=None, label=None, value_labels=None, **kwargs):
        """Constructor."""
        kwargs["field"] = self.field(field)
        super().__init__(label, value_labels, **kwargs)


class CFNestedTermsFacet(CFFacetMixin, NestedTermsFacet):
    """Nested Terms facet for custom fields.

    Works exactly as NestedTermsFacet except that prepends the prefix `custom_fields`
    in the field definition.
    """

    def __init__(self, field=None, label=None, value_labels=None, **kwargs):
        """Constructor."""
        kwargs["field"] = self.field(field)
        super().__init__(label, value_labels, **kwargs)


class DateFacet(LabelledFacetMixin, Facet):
    """Date-based facet using date_histogram aggregation.

    Supports:
    - YYYY
    - YYYY-MM
    - YYYY-MM-DD
    - Ranges: 2014..2020, ..2020, 2014..
    - Explicit bounds: (2014..2020], [2014..2020)

    The facet values are normalized to full date ranges before being sent to
    OpenSearch. Inclusive and exclusive bounds are controlled with brackets:
    "["/"]" include and "("/")" exclude the boundary.

    OpenSearch range operators:
    - gte: greater than or equal (inclusive lower bound)
    - gt: greater than (exclusive lower bound)
    - lte: less than or equal (inclusive upper bound)
    - lt: less than (exclusive upper bound)
    - relation=INTERSECTS: the indexed range overlaps the query range (for
      range fields; here it is included for consistency with range queries)

    Example filter JSON sent to OpenSearch for a filter value `2014-08..2020-03`:
    {
        "range": {
            "metadata.field": {
                "gte": "2014-08-01",
                "lte": "2020-03-31",
                "relation": "INTERSECTS"
            }
        }
    }

    Supports optional ``hard_bounds`` to limit the histogram range, and
    ``match_filter_bounds`` to control how those bounds interact with the
    active filter (see ``_effective_bounds``).
    """

    def __init__(
        self,
        field,
        label=None,
        interval="year",
        format="yyyy",
        separator="..",
        hard_bounds=None,
        match_filter_bounds=False,
        **kwargs,
    ):
        """Constructor."""
        self._field = field
        self._label = label or ""
        self._interval = interval
        self._format = format
        self._separator = separator
        self._hard_bounds = hard_bounds
        self._match_filter_bounds = match_filter_bounds
        self._active_filter_values = None
        self._range_re = re.compile(
            rf"""
            (?P<open>[\(\[])?          # optional opening bracket
            (?P<start>[^\.]*)          # start value
            {re.escape(separator)}     # range separator
            (?P<end>[^\]\)]*)          # end value
            (?P<close>[\)\]])?         # optional closing bracket
            """,
            re.VERBOSE,
        )
        super().__init__(label=label, **kwargs)

    def prepare_aggregation(self, filter_values):
        """Prepare the aggregation by storing active filter values.

        Called before ``get_aggregation`` so that ``_effective_bounds`` can
        adjust ``hard_bounds`` when the filter range extends outside the
        configured bounds.
        """
        self._active_filter_values = filter_values

    def get_aggregation(self):
        """Get the date_histogram aggregation."""
        agg_params = {
            "field": self._field,
            "calendar_interval": self._interval,
            "format": self._format,
            "min_doc_count": 0,
        }
        bounds = self._effective_bounds()
        if bounds:
            agg_params["hard_bounds"] = bounds
        return dsl.A("date_histogram", **agg_params)

    def _effective_bounds(self):
        """Compute effective hard_bounds for the aggregation.

        When ``match_filter_bounds`` is False (default), the configured
        ``hard_bounds`` is used while the filter is within them, and replaced
        with the filter range when the filter extends outside. This keeps the
        histogram showing context around the filter selection.

        When ``match_filter_bounds`` is True, the bounds always match the
        filter range when a filter is active. The histogram focuses strictly
        on the user's selection.

        Examples (with configured ``{"min": "1970", "max": "now/y"}``):

        +----------------+----------------------------+-----------------+
        | Filter         | match_filter_bounds=False  | =True           |
        +================+============================+=================+
        | none           | ``1970..now/y``            | ``1970..now/y`` |
        +----------------+----------------------------+-----------------+
        | ``2000..2026`` | ``1970..now/y``            | ``2000..2026``  |
        +----------------+----------------------------+-----------------+
        | ``1500..1700`` | ``1500..1700``             | ``1500..1700``  |
        +----------------+----------------------------+-----------------+
        """
        if not self._active_filter_values:
            return self._hard_bounds

        for value in self._active_filter_values:
            r = self._normalize_value(value)
            if r is None:
                continue

            if self._match_filter_bounds or self._is_outside_bounds(r):
                new_bounds = {}
                if r["start"]:
                    new_bounds["min"] = self._format_bound(r["start"])
                if r["end"]:
                    new_bounds["max"] = self._format_bound(r["end"])
                return new_bounds or self._hard_bounds

        return self._hard_bounds

    def _is_outside_bounds(self, normalized_filter):
        """Check if a normalized filter range extends outside hard_bounds."""
        if not self._hard_bounds:
            return False

        bounds_min = self._resolve_bound(self._hard_bounds.get("min"), True)
        bounds_max = self._resolve_bound(self._hard_bounds.get("max"), False)
        start = self._effective_date(normalized_filter, is_start=True)
        end = self._effective_date(normalized_filter, is_start=False)

        starts_before = bool(start and bounds_min and start < bounds_min)
        ends_after = bool(end and bounds_max and end > bounds_max)
        return starts_before or ends_after

    def _effective_date(self, normalized_filter, is_start):
        """Compute the actual first/last matching date, mirroring date math rounding."""
        raw = normalized_filter["start_raw" if is_start else "end_raw"]
        normalized = normalized_filter["start" if is_start else "end"]
        inclusive = normalized_filter[
            "start_inclusive" if is_start else "end_inclusive"
        ]
        if not raw or not normalized:
            return None
        if inclusive:
            return normalized
        return self._next_period(raw, is_start)

    @staticmethod
    def _next_period(raw, is_start):
        """Shift a raw date by one period (year/month/day) based on its precision."""
        try:
            dt = isoparse(raw).date()
        except (ValueError, TypeError):
            return None
        length = len(raw)
        if length == len("YYYY"):
            # Year precision: e.g. "1970" → 1971-01-01 (start) or 1969-12-31 (end)
            shifted = date(
                dt.year + (1 if is_start else -1),
                1 if is_start else 12,
                1 if is_start else 31,
            )
        elif length == len("YYYY-MM"):
            # Month precision: shift by one month, handling year wrap
            year, month = dt.year, dt.month
            if is_start:
                year, month = (year + 1, 1) if month == 12 else (year, month + 1)
                shifted = date(year, month, 1)
            else:
                year, month = (year - 1, 12) if month == 1 else (year, month - 1)
                shifted = date(year, month, DateFacet._last_day_of_month(year, month))
        elif length == len("YYYY-MM-DD"):
            # Day precision: simply ±1 day
            shifted = dt + (timedelta(days=1) if is_start else timedelta(days=-1))
        else:
            return None
        return f"{shifted.year:04d}-{shifted.month:02d}-{shifted.day:02d}"

    def _format_bound(self, normalized_date):
        """Format a normalized YYYY-MM-DD date to match the aggregation format."""
        if self._format == "yyyy":
            return normalized_date[: len("YYYY")]
        if self._format == "yyyy-MM":
            return normalized_date[: len("YYYY-MM")]
        if self._format == "yyyy-MM-dd":
            return normalized_date[: len("YYYY-MM-DD")]
        return normalized_date[: len("YYYY")]

    def _resolve_bound(self, value, is_start):
        """Resolve a bounds value to a comparable YYYY-MM-DD string.

        Returns None for dynamic expressions like ``"now/y"`` (never exceeded
        by a filter) and for unsupported types.
        """
        if not value:
            return None
        if isinstance(value, int):
            value = str(value)
        if not isinstance(value, str):
            return None
        if value.startswith("now"):
            return None
        return self._normalize_date(value, is_start)

    def add_filter(self, filter_values):
        """Construct a filter query for the facet."""
        if not filter_values:
            return

        q = None
        for value in filter_values:
            rq = self._build_range_query(value)
            if rq is None:
                continue
            q = rq if q is None else q | rq

        return q

    def _build_range_query(self, value):
        """Build an OpenSearch range query from a value."""
        r = self._normalize_value(value)
        if r is None:
            return None

        es_range = {}

        if r["start_raw"]:
            op = "gte" if r["start_inclusive"] else "gt"
            es_range[op] = self._with_rounding(r["start_raw"])

        if r["end_raw"]:
            op = "lte" if r["end_inclusive"] else "lt"
            es_range[op] = self._with_rounding(r["end_raw"])

        return dsl.Q(
            "range",
            **{
                self._field: {
                    **es_range,
                    "relation": "INTERSECTS",
                }
            },
        )

    @staticmethod
    def _with_rounding(raw):
        """Append OpenSearch date math rounding based on input precision.

        Without rounding, ``(1970..]`` would match dates strictly after
        ``1970-01-01T00:00:00`` (e.g., 1970-06-15). With ``||/y`` rounding,
        ``gt: "1970||/y"`` matches dates after the end of 1970, i.e. starting
        from 1971-01-01 — which is what users expect.
        """
        length = len(raw)
        if length == len("YYYY"):
            return f"{raw}||/y"
        if length == len("YYYY-MM"):
            return f"{raw}||/M"
        if length == len("YYYY-MM-DD"):
            return f"{raw}||/d"
        return raw

    def is_filtered(self, key, filter_values):
        """Check if a histogram bucket year is selected by any range."""
        try:
            year = int(key)
        except ValueError:
            return False

        for value in filter_values:
            r = self._normalize_value(value)
            if r is None:
                continue

            start = self._effective_date(r, is_start=True)
            end = self._effective_date(r, is_start=False)
            if start and year < int(start[:4]):
                continue
            if end and year > int(end[:4]):
                continue
            return True

        return False

    def _normalize_value(self, value):
        """Normalize a value into a range dict."""
        value = value.strip()

        def build_result(start_raw, end_raw, start_inc=True, end_inc=True):
            start = (
                self._normalize_date(start_raw, is_start=True) if start_raw else None
            )
            end = self._normalize_date(end_raw, is_start=False) if end_raw else None
            if start is None and end is None:
                return None
            return {
                "start": start,
                "end": end,
                "start_raw": start_raw,
                "end_raw": end_raw,
                "start_inclusive": start_inc,
                "end_inclusive": end_inc,
            }

        # Single value (no separator)
        if self._separator not in value:
            return build_result(value, value)

        # Range value
        match = self._range_re.fullmatch(value)
        if not match:
            return None

        start_raw = match.group("start").strip() or None
        end_raw = match.group("end").strip() or None

        return build_result(
            start_raw,
            end_raw,
            start_inc=match.group("open") != "(",
            end_inc=match.group("close") != ")",
        )

    def _normalize_date(self, value, is_start):
        """Normalize a date value into YYYY-MM-DD format."""
        value = value.strip()

        try:
            dt = isoparse(value)
        except (ValueError, TypeError):
            return None

        # YYYY
        if re.fullmatch(r"\d{4}", value):
            year = dt.year
            return f"{year:04d}-01-01" if is_start else f"{year:04d}-12-31"

        # YYYY-MM
        if re.fullmatch(r"\d{4}-\d{2}", value):
            year, month = dt.year, dt.month
            if is_start:
                return f"{year:04d}-{month:02d}-01"
            return f"{year:04d}-{month:02d}-{self._last_day_of_month(year, month):02d}"

        # YYYY-MM-DD
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return dt.date().isoformat()

        return None

    @staticmethod
    def _last_day_of_month(year, month):
        """Return the last day of a month."""
        if month == 12:
            return 31
        return (date(year, month + 1, 1) - date(year, month, 1)).days
