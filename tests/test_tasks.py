# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Tasks tests."""

from celery import current_app as current_celery_app
from invenio_indexer.proxies import current_indexer_registry
from invenio_search.engine import dsl

from invenio_records_resources.tasks import manage_indexer_queues


def _search_query(uuid):
    """Creates a query for a UUID."""
    clauses = [dsl.Q("bool", must=[dsl.Q("term", **{"uuid": uuid})])]

    return dsl.Q(
        "bool",
        minimum_should_match=1,
        should=clauses,
    )


def test_manage_indexer_queues(app, service, identity_simple, input_data):
    # register the indexer
    current_indexer_registry.register(service.indexer, service.id)
    channel = current_celery_app.connection().channel()
    # create a record
    item = service.create(identity_simple, input_data)
    service.record_cls.index.refresh()
    uuid = item._record.id

    # send to reindex
    assert service.reindex(identity_simple, search_query=_search_query(uuid))
    # check there is one item in the queue
    queue = service.indexer.mq_queue.bind(channel)
    _, num_messages, _ = queue.queue_declare()
    assert num_messages == 1
    # manage
    manage_indexer_queues()
    # check the queue is empty
    _, num_messages, _ = queue.queue_declare()
    assert num_messages == 0
