# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test Service layer RecordItem."""


def test_has_permissions_to(app, service, identity_simple, input_data):
    item = service.create(identity_simple, input_data)

    permissions = item.has_permissions_to(["read", "update_draft"])

    assert {"can_read": True, "can_update_draft": False} == permissions
