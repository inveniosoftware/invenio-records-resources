# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test Resource Configuration."""

import pytest

from invenio_records_resources.resources import RecordResource, \
    RecordResourceConfig


class ConfigA(RecordResourceConfig):
    pass


class ConfigB(RecordResourceConfig):
    pass


class MyResource(RecordResource):
    default_config = ConfigB


@pytest.fixture(scope='module')
def app_config(app_config):
    """Override pytest-invenio app_config fixture.

    For test purposes we need to enforce some configuration variables before
    endpoints are created.
    """
    app_config["TEST_RESOURCE_CONFIG_1"] = ConfigA
    app_config["TEST_RESOURCE_CONFIG_2"] = (
        "invenio_records_resources.resources.RecordResourceConfig"
    )
    app_config["TEST_RESOURCE_CONFIG_3"] = None

    return app_config


def test_resource_loads_configured_value_config(app):
    MyResource.config_name = "TEST_RESOURCE_CONFIG_1"

    resource = MyResource()

    assert resource.config == ConfigA


def test_resource_loads_configured_string_config(app):
    MyResource.config_name = "TEST_RESOURCE_CONFIG_2"

    resource = MyResource()

    assert resource.config == RecordResourceConfig


def test_resource_loads_default_config(app):
    # Set a config_name that evaluates False
    MyResource.config_name = "TEST_RESOURCE_CONFIG_3"

    resource = MyResource()

    assert resource.config == ConfigB

    # Set a config_name that is not defined
    MyResource.config_name = "TEST_RESOURCE_CONFIG_4"

    resource = MyResource()

    assert resource.config == ConfigB
