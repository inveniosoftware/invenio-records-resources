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
from invenio_app.factory import create_api as _create_api
from invenio_files_rest.models import Location

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


@pytest.fixture()
def location(db, tmp_path):
    """File system location."""
    loc = Location(
        name='testloc',
        uri=str(tmp_path),
        default=True
    )
    db.session.add(loc)
    db.session.commit()
    return loc
