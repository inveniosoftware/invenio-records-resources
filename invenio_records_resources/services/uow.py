# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Unit of work.

Classes were moved to invenio-db.

Used to group multiple service operations into a single atomic unit. The Unit
of Work maintains a list of operations and coordinates the commit, indexing and
task execution.

Note, this is NOT a clean implementation of the UoW design pattern. The
main purpose of the Unit of Work in Invenio is to coordinate when the database
transaction commit is called, and ensure tasks that have to run after the
transaction are executed (such as indexing and running celery tasks).

This ensures that we can group multiple service calls into a single database
transaction and perform the necessary indexing/task execution afterwards.

**When to use?**

You should use the unit of work instead of running an explicit
``db.session.commit()`` or ``db.session.rollback()`` in the code. Basically
any function where you would normally have called a ``db.session.commit()``
should be changed to something like:

.. code-block:: python

    from invenio_records_resources.services.uow import \
        RecordCommitOp, unit_of_work,

    @unit_of_work()
    def create(self, ... , uow=None):
        # ...
        uow.register(RecordCommitOp(record, indexer=self.indexer))
        # ...
        # Do not use `db.session.commit()` in service.

Any private method that need to run operations after the database transaction
commit should take the unit of work as input:

.. code-block:: python

    def _reindex_something(uow, ...):
        # Index after transaction (no record commit)
        uow.register(RecordIndexOp(record))

    def _send_a_task(uow, ...):
        # Run a celery task after the database transaction commit.
        uow.register(TaskOp(my_celery_task, myarg, ... ))


**When not to use?**

If you're not changing the database state there's no need to use the unit of
work. Examples include:

- Reading a record
- Search for records
- Reindex all records - because there's no database transaction involved, and
  the method is also not intended to be grouped together with multiple other
  state changing service calls there's no need to use the unit of work.

**How to group multiple service calls?**

In order to group multiple service calls into one atomic operation you can use
the following pattern:

.. code-block:: python

    from invenio_records_resources.services.uow import UnitOfWork

    with UnitOfWork() as uow:
        # Be careful to always inject "uow" to the service. If not, the
        # service will create its own unit of work and commit.
        service.communities.add(..., uow=uow)
        service.publish(... , uow=uow)
        uow.commit()

If you're not grouping multiple service calls, then simply just call the
service method (and it will commit automatically):

.. code-block:: python

    service.publish(...)

**Writing your own operation?**

You can write your own unit of work operation by subclassing the operation
class and implementing the desired methods:

.. code-block:: python

    from invenio_records_resources.services.uow import Operation

    class BulkIndexOp(Operation):
        def on_commit(self, uow):
            # ... executed after the database transaction commit ...
"""

from celery import current_app

# backwards compatible imports
from invenio_db.uow import (
    ModelCommitOp,
    ModelDeleteOp,
    Operation,
    UnitOfWork,
    unit_of_work,
)

from ..tasks import send_change_notifications

__all__ = ["ModelCommitOp", "ModelDeleteOp", "Operation", "UnitOfWork", "unit_of_work"]


#
# Unit of work operations
#
class RecordCommitOp(Operation):
    """Record commit operation with indexing."""

    def __init__(self, record, indexer=None, index_refresh=False):
        """Initialize the record commit operation."""
        self._record = record
        self._indexer = indexer
        self._index_refresh = index_refresh

    def on_register(self, uow):
        """Commit record (will flush to the database)."""
        self._record.commit()

    def on_commit(self, uow):
        """Run the operation."""
        if self._indexer is not None:
            arguments = {"refresh": True} if self._index_refresh else {}
            self._indexer.index(self._record, arguments=arguments)


class RecordBulkCommitOp(Operation):
    """Record bulk commit operation with indexing."""

    def __init__(self, records, indexer=None, index_refresh=False):
        """Initialize the bulk record commit operation."""
        self._records = records
        self._indexer = indexer
        self._index_refresh = index_refresh

    def on_register(self, uow):
        """Save objects to the session."""
        for record in self._records:
            record.commit()

    def on_commit(self, uow):
        """Run the operation."""
        if self._indexer is not None:
            record_ids = [record.id for record in self._records]
            self._indexer.bulk_index(record_ids)


class RecordIndexOp(RecordCommitOp):
    """Record indexing operation."""

    def on_register(self, uow):
        """Overwrite method to not commit."""
        pass


class RecordBulkIndexOp(Operation):
    """Record bulk indexing operation."""

    def __init__(self, records_iter, indexer=None):
        """Initialize the records bulk index operation.

        :param records_iter: iterable of record ids.
        :param indexer: indexer instance.
        """
        self._records_iter = records_iter
        self._indexer = indexer

    def on_post_commit(self, uow):
        """Run bulk indexing as one of the last operations."""
        if self._indexer is not None:
            self._indexer.bulk_index(self._records_iter)


class RecordDeleteOp(Operation):
    """Record removal operation."""

    def __init__(self, record, indexer=None, force=False, index_refresh=False):
        """Initialize the record delete operation."""
        self._record = record
        self._indexer = indexer
        self._force = force
        self._index_refresh = index_refresh

    def on_register(self, uow):
        """Soft/hard delete record."""
        self._record.delete(force=self._force)

    def on_commit(self, uow):
        """Delete from index."""
        if self._indexer is not None:
            self._indexer.delete(self._record, refresh=self._index_refresh)


class RecordIndexDeleteOp(RecordDeleteOp):
    """Record index delete operation."""

    def on_register(self, uow):
        """Overwrite method to not commit."""
        pass


class IndexRefreshOp(Operation):
    """Search index refresh operation."""

    def __init__(self, indexer, index=None, **kwargs):
        """Initialize the index to be refreshed."""
        self._indexer = indexer
        self._index = index
        self._kwargs = kwargs

    def on_post_commit(self, uow):
        """Run refresh after record commit."""
        self._indexer.refresh(index=self._index, **self._kwargs)


class TaskOp(Operation):
    """A celery task operation.

    Celery tasks are always execute after the entire commit phase.
    """

    def __init__(self, celery_task, *args, **kwargs):
        """Initialize the task operation."""
        self._celery_task = celery_task
        self._args = args
        self._kwargs = kwargs
        self.celery_kwargs = {}

    def on_post_commit(self, uow):
        """Run the post task operation."""
        self._celery_task.apply_async(
            args=self._args, kwargs=self._kwargs, **self.celery_kwargs
        )

    @classmethod
    def for_async_apply(cls, celery_task, args=None, kwargs=None, **celery_kwargs):
        """Create TaskOp that supports apply_async args."""
        temp = cls(celery_task, *(args or tuple()), **(kwargs or {}))
        temp.celery_kwargs = celery_kwargs
        return temp


class TaskRevokeOp(Operation):
    """A celery task stopping operation."""

    def __init__(self, task_id: str) -> None:
        """Initialize the task operation."""
        self.task_id = task_id

    def on_post_commit(self, uow) -> None:
        """Run the revoke post commit."""
        current_app.control.revoke(self.task_id, terminate=True)


class ChangeNotificationOp(Operation):
    """A change notification operation."""

    def __init__(self, record_type, records):
        """Constructor."""
        self._record_type = record_type
        self._records = records

    def on_post_commit(self, uow):
        """Send the notification (run celery task)."""
        send_change_notifications.delay(
            self._record_type,
            [(r.pid.pid_value, str(r.id), r.revision_id) for r in self._records],
        )
