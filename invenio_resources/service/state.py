# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Agent is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""State API."""


# TODO: Would be nice to replace with less generic name than "state"
class RecordState:
    """State object for objects associated with a record."""

    def __init__(self, pid=None, record=None):
        """Initialize the record state."""
        self.id = pid.pid_value
        self.pids = [pid]
        self.record = record

    def is_revision(self, revision_id):
        """Check if record is in a specific revision."""
        return str(self.record.revision_id) == str(revision_id)


class RecordSearchState:
    """State object for objects associated with a record search."""

    def __init__(self, records, total, aggregations):
        """Initialize the record state."""
        self.records = records
        self.total = total
        self.aggregations = aggregations


class TombstoneState(RecordState):
    """State for tombstones."""

    pid = None
    record = None
