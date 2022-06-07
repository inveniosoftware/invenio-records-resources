# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets value labelling."""

from invenio_records.dictutils import dict_lookup


class RecordRelationLabels:
    """Inefficient fetching of relations for facets."""

    def __init__(self, relation, lookup_key):
        """Initialize the labels."""
        self.relation = relation
        self.lookup_key = lookup_key

    def __call__(self, ids):
        """Return the mapping when evaluated."""
        labels = {}

        for id_ in ids:
            labels[id_] = dict_lookup(
                self.relation.pid_field.resolve(id_), self.lookup_key
            )

        return labels
