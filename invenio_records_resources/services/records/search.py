# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Search utilities."""

import itertools
import operator

from elasticsearch_dsl import Q


def terms_filter(field):
    """Create a term filter used for aggregations.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """
    def inner(values):
        return Q('terms', **{field: values})
    return inner


def nested_terms_filter(field, subfield, splitchar):
    """Create a nested term filter used for nested aggregations.

    :param field: Field name.
    :param subfield: Subfield name of a Field.
    :param splitchar: Character dividing the Field and Subfield.
    :returns: Function that returns the Nested terms query.
    """
    def inner(values):
        field_values = {}
        term_queries = []

        # Iterating through aggregation and nested aggregations
        for filter in values:
            # Get the aggregation type
            field_name = filter.split(splitchar)[0]

            # If aggregation type is not present in field_values,
            # add them to dict with a empty list
            if field_name not in field_values:
                field_values[field_name] = []

            # If `splitchar` is present in filter, append the
            # subfield aggregations to the belonging aggregation type key
            if splitchar in filter:
                subfield_value = filter.split(splitchar)[-1]
                field_values[field_name].append(subfield_value)

        # Iterate through aggregation type and
        # create term query with `AND` operation
        for k in field_values.keys():
            if field_values[k]:
                term_queries.append(
                    Q('term', **{field: k}) &
                    Q('terms', **{subfield: field_values[k]})
                )
            else:
                term_queries.append(Q('term', **{field: k}))

        # Return the query after creating a chain of `OR` queries.
        query = list(itertools.accumulate(term_queries, operator.or_))[-1]
        return query

    return inner
