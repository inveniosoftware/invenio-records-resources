# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Persistent identifier status field."""

from invenio_pidstore.models import PersistentIdentifier
from invenio_records.systemfields import SystemField


class PIDStatusField(SystemField):
    """Persistent identifier system field."""

    def __init__(self, key='status'):
        """Initialize the PIDField.

        :param key: Name of key to store the status value in.
        """
        super().__init__(key=key)

    #
    # Data descriptor methods (i.e. attribute access)
    #
    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return self  # returns the field itself.

        return record.pid.status
