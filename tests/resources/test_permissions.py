# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

import json

import pytest
from invenio_accounts.testutils import login_user_via_view
from invenio_records_permissions.generators import Admin
from invenio_records_permissions.policies.records import RecordPermissionPolicy

from invenio_records_resources.resources import RecordResource, \
    RecordResourceConfig
from invenio_records_resources.services import RecordService

HEADERS = {"content-type": "application/json", "accept": "application/json"}


class AdminCanCreatePermissionPolicy(RecordPermissionPolicy):
    """Custom permission policy."""

    can_create = [Admin()]


class CustomRecordResourceConfig(RecordResourceConfig):
    list_route = "/custom-records"


@pytest.fixture(scope="module")
def app_with_custom_permissions(app, record_service_config):
    """Application factory fixture."""

    class CustomRecordServiceConfig(record_service_config):
        """Custom RecordService configuration for tests."""

        permission_policy_cls = AdminCanCreatePermissionPolicy

    # NOTE: This overrides the previously registered endpoints
    custom_bp = RecordResource(
        config=CustomRecordResourceConfig,
        service=RecordService(config=CustomRecordServiceConfig)
    ).as_blueprint("custom_resource")
    app.register_blueprint(custom_bp)
    yield app


@pytest.mark.skip()
def test_create_record_permissions(app_with_custom_permissions, client,
                                   input_record, users):
    """Test record creation."""
    user1 = users['user1']
    user2 = users['user2']
    # Create new record as anonymous
    response = client.post(
        "/custom-records", headers=HEADERS, data=json.dumps(input_record)
    )

    assert response.status_code == 403
    assert response.json["message"] == "Permission denied."
    # Create new record as user with no `admin-access`
    # Login user2
    login_user_via_view(client, email=user2['email'],
                        password=user2['password'], login_url='/login')

    response = client.post(
        "/custom-records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 403
    assert response.json["message"] == "Permission denied."

    # logout user2
    client.post('/logout')

    # Create a new record as a user with `admin-access`
    # Login user1
    login_user_via_view(client, email=user1['email'],
                        password=user1['password'], login_url='/login')
    response = client.post(
        "/custom-records", headers=HEADERS, data=json.dumps(input_record)
    )
    assert response.status_code == 201
    response_fields = response.json.keys()
    fields_to_check = ['pid', 'metadata', 'revision',
                       'created', 'updated', 'links']
    for field in fields_to_check:
        assert field in response_fields
