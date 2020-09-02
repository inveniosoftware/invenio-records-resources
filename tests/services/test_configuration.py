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


class TestServiceConfigA(ServiceConfig):
    pass


class TestServiceConfigB(ServiceConfig):
    pass


class TestService(Service):
    default_config = TestServiceConfigB


@pytest.fixture(scope='module')
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["TEST_SERVICE_CONFIG_1"] = TestServiceConfigA
    app_config["TEST_SERVICE_CONFIG_2"] = (
        "invenio_records_resources.services.RecordServiceConfig"
    )
    app_config["TEST_SERVICE_CONFIG_3"] = None

    return app_config


def test_service_loads_configured_value_config(app):
    TestService.config_name = "TEST_SERVICE_CONFIG_1"

    service = TestService()

    assert service.config == TestServiceConfigA


def test_service_loads_configured_string_config(app):
    TestService.config_name = "TEST_SERVICE_CONFIG_2"

    service = TestService()

    assert service.config == RecordServiceConfig


def test_service_loads_default_config(app):
    # Set a config_name that evaluates False
    TestService.config_name = "TEST_SERVICE_CONFIG_3"

    service = TestService()

    assert service.config == TestServiceConfigB

    # Set a config_name that is not defined
    TestService.config_name = "TEST_SERVICE_CONFIG_4"

    service = TestService()

    assert service.config == TestServiceConfigB
