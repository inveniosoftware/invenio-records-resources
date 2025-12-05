# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2025 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Dynamically created Grant type."""

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser

from invenio_records_resources.factories.factory import RecordTypeFactory
from tests.mock_module.schemas import RecordSchema


class PermissionPolicy(RecordPermissionPolicy):
    """Mock permission policy. All actions allowed."""

    can_search = [AnyUser()]
    can_create = [AnyUser()]
    can_read = [AnyUser()]
    can_update = [AnyUser()]
    can_delete = [AnyUser()]
    can_read_files = [AnyUser()]
    can_update_files = [AnyUser()]


grant_type = RecordTypeFactory(
    "Grant",
    RecordSchema,
    permission_policy_cls=PermissionPolicy,
    service_id="grants",
)


def create_bp(app):
    """Create Grants blueprints."""
    service = grant_type.service_cls(grant_type.service_config_cls)
    resource = grant_type.resource_cls(grant_type.resource_config_cls, service)
    return resource.as_blueprint()
