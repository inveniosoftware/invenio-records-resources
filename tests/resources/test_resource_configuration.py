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


class MyConfig(RecordResourceConfig):
    pass


class MyResource(RecordResource):
    default_config = MyConfig


def test_resource_loads_default_config(app):

    resource = MyResource()

    assert resource.config == MyConfig
