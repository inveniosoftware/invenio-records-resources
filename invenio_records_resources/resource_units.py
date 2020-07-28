# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resource units."""


class IdentifiedRecord:
    """Resource unit representing pid + Record data clump."""

    def __init__(self, pid, record, links):
        """Constructor."""
        self.id = pid.pid_value
        self.pids = [pid]
        self.record = record
        self.links = links

    def is_revision(self, revision_id):
        """Check if record is in a specific revision."""
        return str(self.record.revision_id) == str(revision_id)


class IdentifiedRecords:
    """Resource list representing the result of an IdentifiedRecord search."""

    def __init__(self, records, total, aggregations, links):
        """Constructor.

        :params records: iterable of records
        :params total: total number of records
        :params aggregations: dict of ES aggregations
        :params search_args: dict(page, size, to_idx, from_idx, q)
        """
        self.records = records
        self.total = total
        self.aggregations = aggregations
        self.links = links


class TombstoneState(IdentifiedRecord):
    """State for tombstones."""

    pid = None
    record = None
