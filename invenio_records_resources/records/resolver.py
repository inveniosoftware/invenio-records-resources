# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Simple resolver for using record UUID as a persistent identifier."""

import uuid

from invenio_db import db
from invenio_pidstore.errors import PIDDeletedError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus


class UUIDResolver(object):
    """Resolver that uses the record's UUID instead of a persistent id.

    Normally, you should use invenio_pidstore.resolver:Resolver instead. This
    class bypasses PIDStore and simply uses the UUID of the record as the PID.
    """

    def __init__(self, getter=None, **kwargs):
        """Initialize resolver."""
        self.object_getter = getter

    def resolve(self, pid_value):
        """Resolver that bypasses PIDStore.

        :param pid_value: Persistent identifier.
        :returns: A tuple containing (pid, object).
        """
        if isinstance(pid_value, uuid.UUID):
            object_uuid = pid_value
            pid_value = str(pid_value)
        else:
            object_uuid = uuid.UUID(pid_value)
            pid_value = str(pid_value)

        # todo: raise better error messages?
        # todo: create a pid wrapper
        # todo: handle execptions (e.g. no results for getting record is
        #       detected here)
        return (
            PersistentIdentifier(
                pid_type="recid",
                pid_value=pid_value,
                object_type="rec",
                object_uuid=object_uuid,
                status=PIDStatus.REGISTERED,
            ),
            self.object_getter(object_uuid),
        )


class ModelResolver(object):
    """Resolver for records with an in-table PID.

    This resolver applies to custom records that do not store the PID in
    pidstore, but instead its value is stored in the same db table.
    """

    def __init__(self, record_cls, model_field_name, **kwargs):
        """Initialize resolver."""
        self._record_cls = record_cls
        self.model_field_name = model_field_name

    def resolve(self, pid_value):
        """Resolver that bypasses PIDStore.

        :param pid_value: string.
        :returns: A tuple containing (pid, object).
        """
        with db.session.no_autoflush:  # avoid flushing the current session
            filters = {self.model_field_name: pid_value}
            obj = self._record_cls.model_cls.query.filter_by(**filters).one()
            # get record and pid
            record = self._record_cls(obj.data, model=obj)
            return (record.pid, record)
