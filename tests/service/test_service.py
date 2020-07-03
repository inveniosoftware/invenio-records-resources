# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Agent is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Agents tests."""

from uuid import uuid4

import pytest
from flask_principal import Identity, UserNeed

from invenio_resources.service import RecordService, RecordServiceFactory


def test_service_get(service_cls, identity_simple, fake_record_db):
    """Get a record."""
    for recid, fake_record in fake_record_db.items():
        recstate = service_cls.get(recid, identity=identity_simple)
        assert recstate.record == fake_record
        assert recstate.id == str(recid)

    # test not found
    # test not found
    # test pid resolver errors
    # test permission errors
