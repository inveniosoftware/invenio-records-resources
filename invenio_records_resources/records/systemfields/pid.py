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

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.resolver import Resolver
from invenio_records.systemfields import SystemField, SystemFieldContext
from sqlalchemy import inspect


class PIDFieldContext(SystemFieldContext):
    """PIDField context.

    This class implements the class-level methods available on a PIDField. I.e.
    when you access the field through the class, for instance:

    .. code-block:: python

        Record.pid.resolve('...')
        Record.pid.session_merge(record)
    """

    def resolve(self, pid_value, registered_only=True):
        """Resolve identifier."""
        # Create resolver
        resolver = self.field._resolver_cls(
            pid_type=self.field._pid_type,
            object_type=self.field._object_type,
            getter=self.record_cls.get_record,
            registered_only=registered_only,
        )

        # Resolve
        pid, record = resolver.resolve(pid_value)

        # Store pid in cache on record.
        self.field._set_cache(record, pid)

        return record

    def session_merge(self, record):
        """Merge the PID to the session if not persistent."""
        pid = self.field.obj(record)
        if not inspect(pid).persistent:
            pid = db.session.merge(pid)
            self.field._set_cache(record, pid)


class PIDField(SystemField):
    """Persistent identifier system field."""

    def __init__(self, key='id', provider=None, pid_type=None,
                 object_type='rec', resolver_cls=None, delete=True,
                 create=True):
        """Initialize the PIDField.

        :param key: Name of key to store the pid value in.
        :param provider: A PID provider used to create the internal persistent
            identifier.
        :param pid_type: The persistent identifier type (only used if no
            provider is specified.
        :param pid_type: The resolver to use.
        :param resolver_cls: The resolver class to use for resolving the PID.
        :param delete: Set to True of pid should be automatically deleted.
        :param create: Set to True of pid should be automatically created.
        """
        self._provider = provider
        self._pid_type = provider.pid_type if provider else pid_type
        self._object_type = object_type
        self._resolver_cls = resolver_cls or Resolver
        self._delete = delete
        self._create = create
        super().__init__(key=key)

    #
    # Life-cycle hooks
    #
    def pre_commit(self, record):
        """Called before a record is committed."""
        # Make sure we serialize the pid on record.commit() time as it might
        # have changed.
        pid = getattr(record, self.attr_name)
        if pid is not None:
            self.set_obj(record, pid)

    def post_create(self, record):
        """Called after a record is created."""
        if self._provider is None or not self._create:
            return

        # This uses the data descriptor method __get__() below:
        if getattr(record, self.attr_name) is None:
            # Create a PID if the object doesn't already have one.
            _pid = self._provider.create(
                object_type=self._object_type,
                object_uuid=record.id
            ).pid

            setattr(record, self.attr_name, _pid)

    def post_delete(self, record, force=False):
        """Called after a record is deleted."""
        if self._delete:
            pid = getattr(record, self.attr_name)
            if pid is not None:
                if not inspect(pid).persistent:
                    pid = db.session.merge(pid)
                self._provider(pid).delete()

    #
    # Helpers
    #
    def obj(self, instance):
        """Get the persistent identifier object.

        Uses a cached object if it exists.

        IMPORTANT: By default if the object is created based on the data in the
        record, it is NOT added to the database session, thus the
        PersistentIdentifier object will be in a transient state instead of
        persistent state. This is useful for instance in search queries to
        avoid hitting the database, however if you need to make operations
        on it you should add it to the session using:

        .. code-block::

            Record.pid.session_merge(record)
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

    def set_obj(self, record, pid):
        """Set the object."""
        assert isinstance(pid, PersistentIdentifier)

        # Store data values on the attribute name (e.g. 'pid')
        record[self.attr_name] = {
            'pk': pid.id,
            'pid_type': pid.pid_type,
            'status': str(pid.status),
            'obj_type': pid.object_type,
        }

        # Set ID on desired dictionary key.
        self.set_dictkey(record, pid.pid_value)

        # Cache object
        self._set_cache(record, pid)

    #
    # Data descriptor methods (i.e. attribute access)
    #
    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return PIDFieldContext(self, owner)
        return self.obj(record)

    def __set__(self, record, pid):
        """Set persistent identifier on record."""
        self.set_obj(record, pid)
