# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""
from copy import deepcopy
from datetime import date

import pytest
from flask import Flask
from flask_security.utils import hash_password
from invenio_access.models import ActionUsers
from invenio_access.permissions import superuser_access
from invenio_access.proxies import current_access
from invenio_accounts.models import Role
from invenio_app.factory import create_api as _create_api
from invenio_records_permissions.generators import Admin, AnyUser
from invenio_records_permissions.policies.records import RecordPermissionPolicy

from invenio_records_resources.resources import RecordResource, \
    RecordResourceConfig
from invenio_records_resources.services import RecordService, \
    RecordServiceConfig


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
    app_config["RECORDS_REST_ENDPOINTS"] = {}

    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope="function")
def input_record():
    """Minimal record data as dict coming from the external world."""
    return {
        "_access": {"metadata_restricted": False, "files_restricted": False},
        "_owners": [1],
        "_created_by": 1,
        "title": "A Romans story",
        "description": "A looong description full of lorem ipsums"
    }


@pytest.fixture()
def users(app, db):
    """Create users."""
    def dump_user(user):
        """User object to dict."""
        return {
            'email': user.email,
            'id': user.id,
            'password': password
        }
    password = '123456'
    with db.session.begin_nested():
        datastore = app.extensions['security'].datastore
        # create users
        hashed_password = hash_password(password)
        user1 = datastore.create_user(email='user1@test.com',
                                      password=hashed_password, active=True)
        user2 = datastore.create_user(email='user2@test.com',
                                      password=hashed_password, active=True)
        # Give role to admin
        db.session.add(ActionUsers(action='admin-access',
                                   user=user1))
    db.session.commit()
    return {
        'user1': dump_user(user1),
        'user2': dump_user(user2)
    }


class AnyUserPermissionPolicy(RecordPermissionPolicy):
    """Custom permission policy."""

    can_list = [AnyUser()]
    can_create = [AnyUser()]
    can_read = [AnyUser()]
    can_update = [AnyUser()]
    can_delete = [AnyUser()]
    can_read_files = [AnyUser()]
    can_update_files = [AnyUser()]


@pytest.fixture(scope="module")
def app(app):
    """Application factory fixture."""
    RecordServiceConfig.permission_policy_cls = AnyUserPermissionPolicy
    # NOTE: Because the above is a "global" change, it is picked up by
    #       RecordService() which already uses RecordServiceConfig
    custom_bp = (
        RecordResource(service=RecordService()).as_blueprint("base_resource")
    )
    app.register_blueprint(custom_bp)
    with app.app_context():
        yield app
