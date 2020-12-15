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


class MyConfig(ServiceConfig):
    pass


class MyService(Service):
    default_config = MyConfig


def test_service_loads_constructor_injection(app):
    # Set app config name to load - dynamic import (but won't be loaded because
    # we inject tjhe config via __init__).
    assert MyService(config=MyConfig).config == MyConfig


def test_service_loads_default_config(app):

    assert MyService().config == MyConfig
