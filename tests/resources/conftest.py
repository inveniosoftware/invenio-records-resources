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

from invenio_records_resources.resources import RecordResource
from invenio_records_resources.services import RecordService
from tests.mock_module.config import ServiceConfig
from tests.mock_module.resource import CustomRecordResourceConfig


@pytest.fixture(scope="module")
def service():
    """Record Resource."""
    return RecordService(ServiceConfig)


@pytest.fixture(scope="module")
def record_resource(service):
    """Record Resource."""
    return RecordResource(CustomRecordResourceConfig, service)


@pytest.fixture(scope="module")
def headers():
    """Default headers for making requests."""
    return {
        "content-type": "application/json",
        "accept": "application/json",
    }


@pytest.fixture()
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        "metadata": {"title": "Test"},
    }
