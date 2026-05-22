# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2025 Northwestern University.
# SPDX-License-Identifier: MIT

"""Factories test configuration."""

import pytest
from invenio_app.factory import create_api as _create_api


@pytest.fixture(scope="module")
def extra_entry_points():
    """Extra entry points to load the mock_module features."""
    return {
        "invenio_jsonschemas.schemas": [
            "mock_module_factory = tests.mock_module_factory.jsonschemas",
        ],
        "invenio_search.mappings": [
            "grants = tests.mock_module_factory.mappings",
        ],
        "invenio_base.api_blueprints": [
            "grants = tests.mock_module_factory.grants:create_bp",
        ],
    }


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api
