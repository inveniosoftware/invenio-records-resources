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
from mock_module.resource import Resource, ResourceConfig
from mock_module.service import Service, ServiceConfig


@pytest.fixture(scope="module")
def resource():
    """Resource."""
    # This should work but doesn't because the application context is checked
    # to see if it's been overridden in the config.
    # return Resource(service=Service())
    return Resource(
        config=ResourceConfig,
        service=Service(config=ServiceConfig)
    )


@pytest.fixture(scope="module")
def base_app(base_app, resource):
    """Application factory fixture."""
    base_app.register_blueprint(resource.as_blueprint('mock'))
    # base_app.register_error_handler(HTTPException, handle_http_exception)
    yield base_app
