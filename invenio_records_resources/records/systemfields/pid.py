# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Persistent identifier field.

Notes:
- Should work with UUIDs and PersistentIdentifiers
"""

from invenio_pidstore.models import PersistentIdentifier
from invenio_records.systemfields import SystemField


class PIDField(SystemField):
    """Persistent identifier system field."""

    def __init__(self, key='id', provider=None):
        """Initialize the PIDField.

        :param key: Name of key to store the pid value in.
        """
        self._provider = provider
        super().__init__(key=key)

    #
    # Life-cycle hooks
    #
    def post_create(self, record):
        """Called after a record is created."""
        if self._provider is None:
            return
        # This uses the data descriptor method __get__() below:
        if record.pid is None:
            # Create a PID if the object doesn't already have one.
            record.pid = self._provider.create(
                object_type='rec',
                object_uuid=record.id
            ).pid

    #
    # Object caching on instance
    #
    def _set_cache(self, instance, obj):
        """Set the object on the instance's cache."""
        if not hasattr(instance, '_obj_cache'):
            instance._obj_cache = {}
        instance._obj_cache[self.attr_name] = obj

    def _get_cache(self, instance):
        """Get the object from the instance's cache."""
        return getattr(instance, '_obj_cache', {}).get(self.attr_name)

    #
    # Helpers
    #
    def obj(self, instance):
        """Get the persistent identifier object.

        Uses a cached object if it exists.
        """
        # Check cache
        obj = self._get_cache(instance)
        if obj:
            return obj

        pid_value = self.get_dictkey(instance)
        data = instance.get(self.attr_name)
        # If both have data, we construct the object.
        if pid_value and data:
            obj = PersistentIdentifier(
                id=data.get('pk'),
                pid_type=data.get('status'),
                pid_value=pid_value,
                status=data.get('status'),
                object_type='rec',
                object_uuid=instance.id,
            )
            # Cache object
            self._set_cache(instance, obj)
            return obj
        return None

    #
    # Data descriptor methods (i.e. attribute access)
    #
    def __get__(self, instance, value):
        """Get the persistent identifier."""
        if instance is None:
            return self  # returns the field itself.
        return self.obj(instance)

    def __set__(self, instance, pid):
        """Set persistent identifier on record."""
        assert isinstance(pid, PersistentIdentifier)

        # Store data values on the attribute name (e.g. 'pid')
        instance[self.attr_name] = {
            'type': pid.pid_type,
            'status': str(pid.status),
            'pk': pid.id
        }

        # Set ID on desired dictionary key.
        self.set_dictkey(instance, pid.pid_value)

        # Cache object
        self._set_cache(instance, pid)
