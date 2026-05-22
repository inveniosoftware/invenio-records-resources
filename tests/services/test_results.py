# SPDX-FileCopyrightText: 2021 CERN.
# SPDX-FileCopyrightText: 2021 Northwestern University.
# SPDX-License-Identifier: MIT

"""Test Service layer RecordItem."""


def test_has_permissions_to(app, service, identity_simple, input_data):
    item = service.create(identity_simple, input_data)

    permissions = item.has_permissions_to(["read", "update_draft"])

    assert {"can_read": True, "can_update_draft": False} == permissions
