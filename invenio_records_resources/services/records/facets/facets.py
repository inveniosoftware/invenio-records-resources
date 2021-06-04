# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets types defined."""

from elasticsearch_dsl import A, Q
from elasticsearch_dsl import TermsFacet as TermsFacetBase


class LabelledFacetMixin:
    """Mixin class for overwriting the default get_values() method."""

    def __init__(self, label=None, value_labels=None, **kwargs):
        """Initialize class."""
        self._label = label or ''
        self._value_labels = value_labels
        self._metric = None  # Needed only for ES6 (can be removed later)
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
            out.append({
                "key": key,
                "doc_count": self.get_metric(bucket),
                "is_selected": self.is_filtered(key, filter_values)
            })

        return {'buckets': out}

    def get_labelled_values(self, data, filter_values):
        """Get a labelled version of a bucket."""
        out = []
        # We get the labels first, so that we can efficiently query a resource
        # for all keys in one go, vs querying one by one if needed.
        label_map = self.get_label_mapping(data.buckets)
        for bucket in data.buckets:
            key = self.get_value(bucket)
            out.append({
                "key": key,
                "doc_count": self.get_metric(bucket),
                "label": label_map[key],
                "is_selected": self.is_filtered(key, filter_values)
            })
        return {'buckets': out, 'label': str(self._label)}

    def get_metric(self, bucket):
        """Compatibility for ES6."""
        # This function is defined by elasticsearch-dsl v7, but not v6, so we
        # add it here.
        if self._metric:
            return bucket["metric"]["value"]
        return bucket["doc_count"]


class TermsFacet(LabelledFacetMixin, TermsFacetBase):
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
            ),

            'resource_type': NestedTermsFacet(
                field='metadata.resource_type.type',
                subfield='metadata.resource_type.subtype',
                splitchar='::',
                label=_('Resource types'),
                value_labels=VocabularyL10NLabels(current_service)
            ),
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
        return A(
            'terms',
            field=self._field,
            aggs={
                'inner': A('terms', field=self._subfield)
            }
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
                'publication': ['publication::book', 'publication::journal'],
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

        if subfield_values:
            return (
                Q('term', **{self._field: field_value}) &
                Q('terms', **{self._subfield: subfield_values})
            )
        else:
            return Q('term', **{self._field: field_value})

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
                "is_selected": self.is_filtered(full_key, filter_values)
            }
            if 'inner' in bucket:
                bucket_out['inner'] = self.get_values(
                    bucket.inner,
                    filter_values,
                    key_prefix=full_key
                )
            out.append(bucket_out)
        return {'buckets': out}

    def get_labelled_values(self, data, filter_values, bucket_label=True,
                            key_prefix=None):
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
                "is_selected": self.is_filtered(full_key, filter_values)
            }
            if 'inner' in bucket:
                bucket_out['inner'] = self.get_labelled_values(
                    bucket.inner,
                    filter_values,
                    bucket_label=False,
                    key_prefix=full_key
                )
            out.append(bucket_out)
        ret_val = {'buckets': out}
        if bucket_label:
            ret_val['label'] = str(self._label)
        return ret_val
