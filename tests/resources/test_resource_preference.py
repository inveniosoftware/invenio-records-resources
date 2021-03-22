# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test preference."""

import pytest
from flask import g
from flask_resources.context import resource_requestctx
from mock_module.resource import CustomRecordResource, \
    CustomRecordResourceConfig
from mock_module.service import Service, ServiceConfig

from invenio_records_resources.resources.records.utils import es_preference


@pytest.fixture(scope="module")
def spy_resource():

    class SpyResourceConfig(CustomRecordResourceConfig):
        """Same as Resource except a different list route to not clash."""

        list_route = "/preference-mocks"

    class SpyResource(CustomRecordResource):
        """Same as Resource except that it logs preference."""

        def search(self):
            self.exposed_preference = es_preference()
            identity = g.identity
            hits = self.service.search(
                identity=identity,
                params=resource_requestctx.url_args,
                links_config=self.config.links_config,
                es_preference=self.exposed_preference,
            )
            return hits.to_dict(), 200

    # NOTE: Because this fixture is module scoped, only 1 SpyResource exists
    return SpyResource(
        config=SpyResourceConfig, service=Service(ServiceConfig)
    )


@pytest.fixture(scope="module")
def base_app(base_app, spy_resource):
    """Application factory fixture."""
    custom_bp = spy_resource.as_blueprint("spy_resource")
    base_app.register_blueprint(custom_bp)
    yield base_app


def test_get_es_preference(app, client, headers, spy_resource):
    h = {**headers, 'User-Agent': 'Chrome'}
    environ = {'REMOTE_ADDR': '1.2.3.4'}
    r = client.get('/preference-mocks', headers=h, environ_overrides=environ)

    # Note, the magic value below changes if the algorithm used for computing
    # the preference paramater is changed.
    assert (
        '74658ff283f10c597a9cf452464df78b' == spy_resource.exposed_preference
    )
