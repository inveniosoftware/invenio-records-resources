# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2023 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets types defined."""


from invenio_search.engine import dsl


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


class TermsFacet(LabelledFacetMixin, dsl.TermsFacet):
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
