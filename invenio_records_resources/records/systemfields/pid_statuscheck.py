# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Persistent identifier status field.

The PIDStatusField is used to check if an associated PID is in a given state.
For instance:

.. code-block:: python

    class Record():
        pid = PIDField()
        is_published = PIDStatusCheckField('pid', status=PIDStatus.REGISTERED)

"""

from invenio_records.dictutils import dict_lookup, dict_set, parse_lookup_key
from invenio_records.systemfields import SystemField


class PIDStatusCheckField(SystemField):
    """PID status field which checks against an expected status."""

    def __init__(self, key="pid", status=None, dump=False):
        """Initialize the PIDField.

        :param key: Attribute name of the PIDField to use for status check.
        :param status: The status or list of statuses which will return true.
        :param dump: Dump the status check in the index. Default to False.
        """
        super().__init__(key=key)
        assert status, "You must provide a PIDStatus to test against."
        if not isinstance(status, list):
            status = [status]
        self._pid_status = status
        self._dump = dump

    #
    # Data descriptor methods (i.e. attribute access)
    #
    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return self  # returns the field itself.
        pid = getattr(record, self.key)
        return pid.status in self._pid_status

    def pre_dump(self, record, data, **kwargs):
        """Called before a record is dumped in a secondary storage system."""
        if self._dump:
            dict_set(data, self.attr_name, getattr(record, self.attr_name))

    def pre_load(self, data, **kwargs):
        """Called before a record is dumped in a secondary storage system."""
        if self._dump:
            keys = parse_lookup_key(self.attr_name)
            parent = dict_lookup(data, keys, parent=True)
            parent.pop(keys[-1], None)
