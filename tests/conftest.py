# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
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
from invenio_app.factory import create_api as _create_api
from invenio_files_rest.models import Location
from kombu.compat import Consumer
from mock_module.config import MockFileServiceConfig

from invenio_records_resources.services import FileService

pytest_plugins = ("celery.contrib.pytest", )


@pytest.fixture(scope="module")
def extra_entry_points():
    """Extra entry points to load the mock_module features."""
    return {
        'invenio_db.model': [
            'mock_module = mock_module.models',
        ],
        'invenio_jsonschemas.schemas': [
            'mock_module = mock_module.jsonschemas',
        ],
        'invenio_search.mappings': [
            'records = mock_module.mappings',
        ]
    }


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope='function')
def queue(app):
    """Declare an clean the indexer queue."""
    # TODO: Move this fixture to pytest-invenio
    queue = app.config['INDEXER_MQ_QUEUE']

    with establish_connection() as c:
        q = queue(c)
        q.declare()
        q.purge()

    return queue


@pytest.fixture(scope='function')
def consumer(app, queue):
    """Get a consumer on the queue object for testing bulk operations."""
    # TODO: Move this fixture to pytest-invenio
    with establish_connection() as c:
        yield Consumer(
            connection=c,
            queue=app.config['INDEXER_MQ_QUEUE'].name,
            exchange=app.config['INDEXER_MQ_EXCHANGE'].name,
            routing_key=app.config['INDEXER_MQ_ROUTING_KEY'],
        )


@pytest.fixture(scope="module")
def file_service():
    """File service shared fixture."""
    return FileService(MockFileServiceConfig)
