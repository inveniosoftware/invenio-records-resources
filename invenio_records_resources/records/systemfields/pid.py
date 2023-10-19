# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
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
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.resolver import Resolver
from invenio_records.systemfields import (
    ModelField,
    RelatedModelField,
    RelatedModelFieldContext,
)
from sqlalchemy import inspect

from ..api import PersistentIdentifierWrapper
from ..providers import ModelPIDProvider
from ..resolver import ModelResolver


class PIDFieldContext(RelatedModelFieldContext):
    """PIDField context.

    This class implements the class-level methods available on a PIDField. I.e.
    when you access the field through the class, for instance:

    .. code-block:: python

        Record.pid.resolve('...')
        Record.pid.session_merge(record)
    """

    def resolve(self, pid_value, registered_only=True, with_deleted=False):
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
        # Drafts of published records are soft-deleted and the resolver will
        # return a deleted record because the PID is registered (record is
        # published). We do not want to return deleted records so we raise
        # PID does not exists error.
        if not with_deleted and record.is_deleted:
            raise PIDDoesNotExistError(self.field._pid_type, pid_value)

        # Store pid in cache on record.
        self.field._set_cache(record, pid)

        return record


class PIDField(RelatedModelField):
    """Persistent identifier system field."""

    def __init__(
        self,
        key="id",
        provider=None,
        pid_type=None,
        object_type="rec",
        resolver_cls=None,
        delete=True,
        create=True,
        context_cls=PIDFieldContext,
    ):
        """Initialize the PIDField.

        :param key: Name of key to store the pid value in.
        :param provider: A PID provider used to create the internal persistent
            identifier.
        :param pid_type: The persistent identifier type (only used if no
            provider is specified).
        :param object_type: The object type of the persistent identifier.
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
        super().__init__(
            PersistentIdentifier,
            key=key,
            dump=self.dump_obj,
            load=self.load_obj,
            context_cls=context_cls,
        )

    def create(self, record):
        """Method to create a new persistent identifier for the record."""
        # This uses the fields __get__() data descriptor method below
        pid = getattr(record, self.attr_name)
        if pid is None:
            # Create a PID if the object doesn't already have one.
            pid = self._provider.create(
                object_type=self._object_type,
                object_uuid=record.id,
                record=record,
            ).pid

            # Set using the __set__() method
            setattr(record, self.attr_name, pid)
        return pid

    def delete(self, record):
        """Method to delete a persistent identifier for the record."""
        pid = getattr(record, self.attr_name)
        if pid is not None:
            if not inspect(pid).persistent:
                pid = db.session.merge(pid)
            self._provider(pid).delete()

    #
    # Life-cycle hooks
    #
    def post_create(self, record):
        """Called after a record is created."""
        if self._provider and self._create:
            self.create(record)

    def post_delete(self, record, force=False):
        """Called after a record is deleted."""
        if self._delete:
            self.delete(record)

    #
    # Helpers
    #
    @staticmethod
    def load_obj(field, record):
        """Serializer the object into a record."""
        pid_value = field.get_dictkey(record)
        data = record.get(field.attr_name)

        # If we have both data and pid_value, we construct the object:
        if pid_value and data:
            obj = PersistentIdentifier(
                id=data.get("pk"),
                pid_type=data.get("pid_type"),
                pid_value=pid_value,
                status=data.get("status"),
                object_type=data.get("obj_type"),
                object_uuid=record.id,
            )
            return obj
        return None

    @staticmethod
    def dump_obj(field, record, pid):
        """Set the object."""
        assert isinstance(pid, PersistentIdentifier)

        # Store data values on the attribute name (e.g. 'pid')
        record[field.attr_name] = {
            "pk": pid.id,
            "pid_type": pid.pid_type,
            "status": str(pid.status),
            "obj_type": pid.object_type,
        }

        # Set ID on desired dictionary key.
        field.set_dictkey(record, pid.pid_value)


class ModelPIDFieldContext(PIDFieldContext):
    """Context for ModelPIDField.

    This class implements the class-level methods available on a PIDField. I.e.
    when you access the field through the class, for instance:

    .. code-block:: python

        Record.pid.resolve('...')
        Record.pid.session_merge(record)
    """

    def resolve(self, pid_value, registered_only=True):
        """Resolve identifier."""
        resolver = self.field._resolver_cls(
            self._record_cls, self.field.model_field_name
        )
        pid, record = resolver.resolve(pid_value)
        self.field._set_cache(record, pid)

        return record

    def create(self, record):
        """Method to create a new persistent identifier for the record."""
        # pop from metadata
        pid_value = record.pop(self.field.model_field_name)
        self.field._provider.create(pid_value, record, self.field.model_field_name)

    def session_merge(self, record):
        """Inactivate session merge since it all belongs to the same db obj."""
        pass


class ModelPIDField(ModelField):
    """PID field in a db column on the record model."""

    def __init__(
        self,
        model_field_name="pid",
        provider=ModelPIDProvider,
        resolver_cls=ModelResolver,
        context_cls=ModelPIDFieldContext,
    ):
        """Initialise the dict field.

        :param key: Name of key to store the pid value in.
        """
        self._provider = provider
        self._resolver_cls = resolver_cls
        self._context_cls = context_cls
        super().__init__(
            model_field_name=model_field_name,
        )

    #
    # Data descriptor
    #
    def __get__(self, record, owner=None):
        """Accessing the attribute."""
        # Class access
        if record is None:
            return self._context_cls(self, owner)
        # Instance access
        pid_value = getattr(record.model, self.model_field_name)
        if not pid_value:
            return None

        return PersistentIdentifierWrapper(pid_value)
