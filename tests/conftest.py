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
from invenio_records_resources.service import RecordService, \
    RecordServiceConfig


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return _create_api


# FIXME: this two should come from `invenio-rdm-records`
# However, this module should not be RDM dependent
@pytest.fixture(scope="function")
def minimal_input_record():
    """Minimal record data as dict coming from the external world."""
    return {
        "_access": {"metadata_restricted": False, "files_restricted": False},
        "_owners": [1],
        "_created_by": 1,
        "access_right": "open",
        "resource_type": {"type": "image", "subtype": "image-photo"},
        # Technically not required
        "creators": [],
        "titles": [
            {"title": "A Romans story", "type": "Other", "lang": "eng"}
        ],
    }


@pytest.fixture(scope="function")
def minimal_record(minimal_input_record):
    """Dictionary with the minimum required fields to create a record.

    It fills in the missing and post_loaded fields.
    """
    record = deepcopy(minimal_input_record)
    record["publication_date"] = date.today().isoformat()
    record["_publication_date_search"] = date.today().isoformat()
    return record


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


class AdminCanCreatePermissionPolicy(RecordPermissionPolicy):
    """Custom permission policy."""

    can_create = [Admin()]


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
    RecordService.config = RecordServiceConfig
    custom_bp = RecordResource(
        service_cls=RecordService).as_blueprint("base_resource")
    app.register_blueprint(custom_bp)
    with app.app_context():
        yield app


@pytest.fixture(scope="module")
def app_with_custom_permissions(app):
    """Application factory fixture."""
    RecordServiceConfig.permission_policy_cls = AdminCanCreatePermissionPolicy
    RecordService.config = RecordServiceConfig
    custom_bp = RecordResource(
        service_cls=RecordService).as_blueprint("custom_resource")
    app.register_blueprint(custom_bp)
    yield app
