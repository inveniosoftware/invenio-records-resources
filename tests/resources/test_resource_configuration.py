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


class TestResourceConfigA(RecordResourceConfig):
    pass


class TestResourceConfigB(RecordResourceConfig):
    pass


class TestResource(RecordResource):
    default_config = TestResourceConfigB


@pytest.fixture(scope='module')
def app_config(app_config):
    """Override pytest-invenio app_config fixture.

    For test purposes we need to enforce some configuration variables before
    endpoints are created.

    invenio-records-rest is imported from invenio-records-permissions, so
    we need to disable its default endpoint, until we are completely
    decoupled from invenio-records-rest. Issue:
    https://github.com/inveniosoftware/invenio-records-permissions/issues/51
    """
    app_config["TEST_RESOURCE_CONFIG_1"] = TestResourceConfigA
    app_config["TEST_RESOURCE_CONFIG_2"] = (
        "invenio_records_resources.resources.RecordResourceConfig"
    )
    app_config["TEST_RESOURCE_CONFIG_3"] = None

    return app_config


def test_resource_loads_configured_value_config(app):
    TestResource.config_name = "TEST_RESOURCE_CONFIG_1"

    resource = TestResource()

    assert resource.config == TestResourceConfigA


def test_resource_loads_configured_string_config(app):
    TestResource.config_name = "TEST_RESOURCE_CONFIG_2"

    resource = TestResource()

    assert resource.config == RecordResourceConfig


def test_resource_loads_default_config(app):
    # Set a config_name that evaluates False
    TestResource.config_name = "TEST_RESOURCE_CONFIG_3"

    resource = TestResource()

    assert resource.config == TestResourceConfigB

    # Set a config_name that is not defined
    TestResource.config_name = "TEST_RESOURCE_CONFIG_4"

    resource = TestResource()

    assert resource.config == TestResourceConfigB
