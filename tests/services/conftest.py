# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

import pytest
from celery.messaging import establish_connection
from invenio_cache import current_cache
from kombu import Queue
from kombu.compat import Consumer
from mock_module.api import Record, RecordWithFiles


@pytest.fixture(scope="function")
def queue_config(service):
    """Declare queue configuration (name, exchange and routing_key)."""
    # TODO: Move this fixture to pytest-invenio
    config = {
        "name": service.config.indexer_queue_name,
    }
    return config


@pytest.fixture(scope="function")
def queue(app, queue_config):
    """Declare an clean the indexer queue."""
    # TODO: Move this fixture to pytest-invenio
    queue = Queue(
        name=queue_config.get("name") or "indexer",
        exchange=(queue_config.get("exchange") or app.config["INDEXER_MQ_EXCHANGE"]),
        routing_key=(
            queue_config.get("routing_key") or app.config["INDEXER_MQ_ROUTING_KEY"]
        ),
    )

    with establish_connection() as c:
        q = queue(c)
        q.declare()
        q.purge()

    return queue


@pytest.fixture(scope="function")
def consumer(app, queue):
    """Get a consumer on the queue object for testing bulk operations."""
    # TODO: Move this fixture to pytest-invenio
    with establish_connection() as c:
        yield Consumer(
            connection=c,
            queue=queue.name,
            exchange=queue.exchange.name,
            routing_key=queue.routing_key,
        )


@pytest.fixture()
def example_record(app, db, input_data):
    """Example data layer record."""
    record = Record.create({}, **input_data)
    db.session.commit()
    return record


@pytest.fixture()
def example_file_record(db, input_data):
    """Example record."""
    record = RecordWithFiles.create({}, **input_data)
    record.commit()
    db.session.commit()
    return record


# FIXME: https://github.com/inveniosoftware/pytest-invenio/issues/30
@pytest.fixture()
def cache():
    """Empty cache."""
    try:
        yield current_cache
    finally:
        current_cache.clear()
