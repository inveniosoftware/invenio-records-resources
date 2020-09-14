# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Persistent identifier field.

The PIDField serializes a PersistentIdentifer object into a structure that
looks like below:

.. code-block:: python

    {
        'id': '12345-abcde',
        'pid': {
            'pk': 1,
            'pid_type': 'recid',
            'obj_type': 'rec',
            'status': 'R',
        }
    }

- The PID value is stored in ``id``, but can be changed using the ``key``
argument. For instance, the folowing will also put the ``id`` below the ``pid``
key in the record:

.. code-block:: python

    class Record():
        pid = PIDField('pid.id')

"""

from invenio_pidstore.models import PersistentIdentifier
from invenio_records.systemfields import SystemField


class PIDField(SystemField):
    """Persistent identifier system field."""

    def __init__(self, key='id', provider=None, pid_type=None,
                 object_type='rec'):
        """Initialize the PIDField.

        :param key: Name of key to store the pid value in.
        :param provider: A PID provider used to create the internal persistent
            identifier.
        :param pid_type: The persistent identifier type (only used if no
            provider is specified.
        """
        self._provider = provider
        self._pid_type = provider.pid_type if provider else pid_type
        self._object_type = object_type
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
                object_type=self._object_type,
                object_uuid=record.id
            ).pid

    # TODO: Add a resolve(val) method, that can be access from the record:
    # Record.pid.resolve('12345-12345'); then we can get rid of the resolver
    # on the recordservice(config)?.

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

        # If we have both data and pid_value, we construct the object:
        if pid_value and data:
            obj = PersistentIdentifier(
                id=data.get('pk'),
                pid_type=data.get('pid_type'),
                pid_value=pid_value,
                status=data.get('status'),
                object_type=data.get('obj_type'),
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
            'pk': pid.id,
            'pid_type': pid.pid_type,
            'status': str(pid.status),
            'obj_type': pid.object_type,
        }

        # Set ID on desired dictionary key.
        self.set_dictkey(instance, pid.pid_value)

        # Cache object
        self._set_cache(instance, pid)

    #
    # Object caching on instance
    #

    # TODO: Move to Invenio-Records as a global cache that can be used by
    # system fields.
    def _set_cache(self, instance, obj):
        """Set the object on the instance's cache."""
        if not hasattr(instance, '_obj_cache'):
            instance._obj_cache = {}
        instance._obj_cache[self.attr_name] = obj

    def _get_cache(self, instance):
        """Get the object from the instance's cache."""
        return getattr(instance, '_obj_cache', {}).get(self.attr_name)
