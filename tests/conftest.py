# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2023 CERN.
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
from flask_principal import Identity, Need, UserNeed
from invenio_access import ActionRoles, superuser_access
from invenio_accounts.models import Role
from invenio_app.factory import create_api as _create_api
from mock_module.config import MockFileServiceConfig, ServiceConfig

from invenio_records_resources.services import FileService, RecordService

pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(scope="module")
def app_config(app_config):
    """Override pytest-invenio app_config fixture.

    Needed to set the fields on the custom fields schema.
    """
    app_config["RECORDS_RESOURCES_FILES_ALLOWED_DOMAINS"] = [
        "inveniordm.test",
    ]

    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
        "F": "Fetch",
        "R": "Remote",
    }

    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"

    app_config[
        "RECORDS_REFRESOLVER_CLS"
    ] = "invenio_records.resolver.InvenioRefResolver"
    app_config[
        "RECORDS_REFRESOLVER_STORE"
    ] = "invenio_jsonschemas.proxies.current_refresolver_store"

    return app_config


@pytest.fixture(scope="module")
def extra_entry_points():
    """Extra entry points to load the mock_module features."""
    return {
        "invenio_db.model": [
            "mock_module = mock_module.models",
        ],
        "invenio_jsonschemas.schemas": [
            "mock_module = mock_module.jsonschemas",
        ],
        "invenio_search.mappings": [
            "records = mock_module.mappings",
        ],
    }


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope="module")
def file_service():
    """File service shared fixture."""
    return FileService(MockFileServiceConfig)


@pytest.fixture(scope="module")
def service(appctx):
    """Service instance."""
    return RecordService(ServiceConfig)


@pytest.fixture(scope="function")
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        "metadata": {"title": "Test", "type": {"type": "test"}},
    }


@pytest.fixture(scope="module")
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    return i


@pytest.fixture()
def superuser_role_need(db):
    """Store 1 role with 'superuser-access' ActionNeed.

    WHY: This is needed because expansion of ActionNeed is
         done on the basis of a User/Role being associated with that Need.
         If no User/Role is associated with that Need (in the DB), the
         permission is expanded to an empty list.
    """
    role = Role(name="superuser-access")
    db.session.add(role)

    action_role = ActionRoles.create(action=superuser_access, role=role)
    db.session.add(action_role)

    db.session.commit()

    return action_role.need


@pytest.fixture()
def superuser(UserFixture, app, db, superuser_role_need):
    """Superuser."""
    u = UserFixture(
        email="superuser@inveniosoftware.org",
        password="superuser",
    )
    u.create(app, db)

    datastore = app.extensions["security"].datastore
    _, role = datastore._prepare_role_modify_args(u.user, "superuser-access")

    datastore.add_role_to_user(u.user, role)
    db.session.commit()
    return u


@pytest.fixture()
def superuser_identity(superuser_role_need):
    """Superuser identity fixture."""
    identity = Identity(1)
    identity.provides.add(superuser_role_need)
    return identity
