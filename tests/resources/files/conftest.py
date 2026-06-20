# SPDX-FileCopyrightText: 2020-2021 CERN.
# SPDX-FileCopyrightText: 2021 Northwestern University.
# SPDX-FileCopyrightText: 2025 CESNET.
# SPDX-License-Identifier: MIT

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

import pytest
from invenio_cache import current_cache

from invenio_records_resources.services import RecordService
from tests.mock_module.api import RecordWithFiles
from tests.mock_module.config import ServiceWithFilesConfig


@pytest.fixture(scope="module")
def service():
    """Service with files instance."""
    return RecordService(ServiceWithFilesConfig)


@pytest.fixture(scope="module")
def base_app(base_app, service, file_service):
    """Application factory fixture."""
    registry = base_app.extensions["invenio-records-resources"].registry
    registry.register(service, service_id="mock-records")
    registry.register(file_service, service_id="mock-files")
    yield base_app


@pytest.fixture()
def example_record(app, db, service, input_data, identity_simple, location):
    """Example data layer record."""
    input_data["files"] = {"enabled": True}
    return service.create(identity_simple, input_data)


@pytest.fixture()
def example_file_record(db, input_data, location):
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
