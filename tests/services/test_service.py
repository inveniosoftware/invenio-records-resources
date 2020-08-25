# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests."""


def test_service_read(app, service_cls, identity_simple, fake_record_db):
    """Get a record."""
    service = service_cls()
    for recid, fake_record in fake_record_db.items():
        recstate = service.read(identity_simple, recid)
        assert recstate.record == fake_record
        assert recstate.id == str(recid)
