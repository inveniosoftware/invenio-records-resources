# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests."""


def test_service_get(app, service_cls, identity_simple, fake_record_db):
    """Get a record."""
    service = service_cls()
    for recid, fake_record in fake_record_db.items():
        recstate = service.read(recid, identity=identity_simple)
        assert recstate.record == fake_record
        assert recstate.id == str(recid)

    # test not found
    # test not found
    # test pid resolver errors
    # test permission errors
