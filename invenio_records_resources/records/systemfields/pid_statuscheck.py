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

from invenio_pidstore.models import PIDStatus
from invenio_records.systemfields import SystemField


class PIDStatusCheckField(SystemField):
    """PID status field which checks against an expected status."""

    def __init__(self, key='pid', status=None):
        """Initialize the PIDField.

        :param key: Attribute name of the PIDField to use for status check.
        :param status: The status or list of statuses which will return true.
        """
        super().__init__(key=key)
        assert status, "You must provide a PIDStatus to test against."
        if not isinstance(status, list):
            status = [status]
        self._pid_status = status

    #
    # Data descriptor methods (i.e. attribute access)
    #
    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return self  # returns the field itself.
        pid = getattr(record, self.key)
        return pid.status in self._pid_status
