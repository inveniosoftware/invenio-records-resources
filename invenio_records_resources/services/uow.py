# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Unit of work.

Used to group multiple service operations into a single atomic unit. The Unit
of Work maintains a list of operations and coordinates the commit, indexing and
task execution.

Note, this is NOT a clean implementation of the UoW design pattern. The
main purpose of the Unit of Work in Invenio is to coordinate when the database
transaction commit is called, and ensure tasks that have to run after the
transcation are executed (such as indexing and running celery tasks).

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


from functools import wraps

from invenio_db import db

from ..tasks import send_change_notifications


#
# Unit of work operations
#
class Operation:
    """Base class for unit of work operations."""

    def on_register(self, uow):
        """Called upon operation registration."""
        pass

    def on_commit(self, uow):
        """Called in the commit phase (after the transaction is committed)."""
        pass

    def on_post_commit(self, uow):
        """Called right after the commit phase."""
        pass

    def on_rollback(self, uow):
        """Called in the rollback phase (after the transaction rollback)."""
        pass

    def on_post_rollback(self, uow):
        """Called right after the rollback phase."""
        pass


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


class RecordIndexOp(RecordCommitOp):
    """Record indexing operation."""

    def on_register(self, uow):
        """Overwrite method to not commit."""
        pass


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

    def on_post_commit(self, uow):
        """Run the post task operation."""
        self._celery_task.delay(*self._args, **self._kwargs)


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


#
# Unit of work context manager
#
class UnitOfWork:
    """Unit of work context manager.

    Note, the unit of work does not currently take duplication of work into
    account. Thus, you can e.g. add two record commit operations of the same
    record which will then index the record twice, even though only one time
    is needed.
    """

    def __init__(self, session=None):
        """Initialize unit of work context."""
        self._session = session or db.session
        self._operations = []
        self._dirty = False

    def __enter__(self):
        """Entering the context."""
        return self

    def __exit__(self, exc_type, *args):
        """Rollback on exception."""
        if exc_type is not None:
            self.rollback()
            self._mark_dirty()

    @property
    def session(self):
        """The SQLAlchemy database session associated with this UoW."""
        return self._session

    def _mark_dirty(self):
        """Mark the unit of work as dirty."""
        if self._dirty:
            raise RuntimeError("The unit of work is already committed or rolledback.")
        self._dirty = True

    def commit(self):
        """Commit the unit of work."""
        self.session.commit()
        # Run commit operations
        for op in self._operations:
            op.on_commit(self)
        # Run post commit operations
        for op in self._operations:
            op.on_post_commit(self)
        self._mark_dirty()

    def rollback(self):
        """Rollback the database session."""
        self.session.rollback()
        # Run rollback operations
        for op in self._operations:
            op.on_rollback(self)
        # Run post rollback operations
        for op in self._operations:
            op.on_post_rollback(self)

    def register(self, op):
        """Register an operation."""
        # Run on register
        op.on_register(self)
        # Append to list of operations.
        self._operations.append(op)


def unit_of_work(**kwargs):
    """Decorator to auto-inject a unit of work if not provided.

    If no unit of work is provided, this decorator will create a new unit of
    work and commit it after the function has been executed.

    .. code-block:: python

        @unit_of_work()
        def aservice_method(self, ...., uow=None):
            # ...
            uow.register(...)

    """

    def decorator(f):
        @wraps(f)
        def inner(self, *args, **kwargs):
            if "uow" not in kwargs:
                # Migration path - start a UoW and commit
                with UnitOfWork(db.session) as uow:
                    kwargs["uow"] = uow
                    res = f(self, *args, **kwargs)
                    uow.commit()
                    return res
            else:
                return f(self, *args, **kwargs)

        return inner

    return decorator
