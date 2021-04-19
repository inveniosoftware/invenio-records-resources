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
from invenio_records_permissions.generators import AnyUser
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

    # factory use
    grant_type = RecordTypeFactory(
        "Grant", RecordSchema, permission_policy_cls=PermissionPolicy
    )
    db.create_all()

    input_data = {
        "metadata": {
            "title": "Test",
        },
    }

    service = grant_type.service_cls(grant_type.service_config_cls)

    # Create an item
    item = service.create(identity_simple, input_data)
    id_ = item.id

    # Read it
    read_item = service.read(id_, identity_simple)
    assert item.id == read_item.id
    assert item.data == read_item.data

    # Refresh to make changes live
    grant_type.record_cls.index.refresh()

    # Search it
    res = service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 1
    assert list(res.hits)[0] == read_item.data
