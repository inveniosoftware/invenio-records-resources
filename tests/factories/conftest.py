# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Factories test configuration."""

import pytest
from invenio_app.factory import create_api as _create_api


@pytest.fixture(scope="module")
def extra_entry_points():
    """Extra entry points to load the mock_module features."""
    return {
        # to be verified if needed, since the models are dynamically created
        "invenio_db.model": [
            "mock_module_factory = tests.mock_module_factory.grant",
        ],
        "invenio_jsonschemas.schemas": [
            "mock_module_factory = tests.mock_module_factory.jsonschemas",
        ],
        "invenio_search.mappings": [
            "grants = tests.mock_module_factory.mappings",
        ],
    }


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api
