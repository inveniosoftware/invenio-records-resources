# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test Service Configuration."""

import pytest

from invenio_records_resources.services import RecordServiceConfig, Service, \
    ServiceConfig


#
# Helper classes
#
class ConfigA(ServiceConfig):
    pass


class ConfigB(ServiceConfig):
    pass


class MyService(Service):
    default_config = ConfigB


#
# Fixtures
#
@pytest.fixture(scope='module')
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["TEST_SERVICE_CONFIG_1"] = ConfigA
    app_config["TEST_SERVICE_CONFIG_2"] = (
        "invenio_records_resources.services.RecordServiceConfig"
    )
    app_config["TEST_SERVICE_CONFIG_3"] = None
    return app_config


#
# Tests
#
def test_service_loads_configured_value_config(app):
    # Set app config name to load -  explicit class
    MyService.config_name = "TEST_SERVICE_CONFIG_1"
    assert MyService().config == ConfigA


def test_service_loads_configured_string_config(app):
    # Set app config name to load - dynamic import
    MyService.config_name = "TEST_SERVICE_CONFIG_2"
    assert MyService().config == RecordServiceConfig


def test_service_loads_constructor_injection(app):
    # Set app config name to load - dynamic import (but won't be loaded because
    # we inject tjhe config via __init__).
    MyService.config_name = "TEST_SERVICE_CONFIG_2"
    assert MyService(config=ConfigA).config == ConfigA


def test_service_loads_default_config(app):
    # Set a config_name that evaluates False
    MyService.config_name = "TEST_SERVICE_CONFIG_3"
    assert MyService().config == ConfigB

    # Set a config_name that is not defined
    MyService.config_name = "TEST_SERVICE_CONFIG_4"
    assert MyService().config == ConfigB
