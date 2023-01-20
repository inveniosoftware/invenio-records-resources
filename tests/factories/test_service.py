# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, Disable
from mock_module.schemas import RecordSchema

from invenio_records_resources.factories.factory import RecordTypeFactory


def test_simple_flow(app, identity_simple, db):
    """Create a record."""

    class PermissionPolicy(RecordPermissionPolicy):
        """Mock permission policy. All actions allowed."""

        can_search = [AnyUser()]
        can_create = [AnyUser()]
        can_read = [AnyUser()]
        can_update = [AnyUser()]
        can_delete = [AnyUser()]
        can_read_files = [AnyUser()]
        can_update_files = [AnyUser()]

    class DenyAllPermissionPolicy(RecordPermissionPolicy):
        """Mock permission policy. All actions denied."""

        can_search = [Disable()]
        can_create = [Disable()]
        can_read = [Disable()]
        can_update = [Disable()]
        can_delete = [Disable()]
        can_read_files = [Disable()]
        can_update_files = [Disable()]

    # factory use
    grant_type = RecordTypeFactory(
        "Grant",
        RecordSchema,
        permission_policy_cls=PermissionPolicy,
        service_id="grants",
    )
    db.create_all()

    input_data = {
        "metadata": {
            "title": "Test",
        },
    }

    service = grant_type.service_cls(grant_type.service_config_cls)
    assert service.id == "grants"
    assert service.config.service_id == "grants"
    assert service.config.indexer_queue_name == "grants"

    # Create an item
    item = service.create(identity_simple, input_data)
    id_ = item.id

    # Read it
    read_item = service.read(identity_simple, id_)
    assert item.id == read_item.id
    assert item.data == read_item.data

    # Refresh to make changes live
    grant_type.record_cls.index.refresh()

    # Search it
    res = service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 1
    assert list(res.hits)[0] == read_item.data

    # Check to see if the document exists
    assert (
        service.exists(identity_simple, id_) == True
    )  # Valid ID AND valid permissions
    assert (
        service.exists(identity_simple, "not-a-valid-id") == False
    )  # Invalid ID AND valid permissions

    # Further Tesing for when user does not have permission to read
    service.permission_policy = DenyAllPermissionPolicy

    # Check to see if the document exists when we have no permissions
    assert (
        service.exists(identity_simple, id_) == False
    )  # Valid ID AND invalid permissions
    assert (
        service.exists(identity_simple, "not-a-valid-id") == False
    )  # Invalid ID AND invalid permissions
