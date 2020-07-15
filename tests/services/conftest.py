# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""
from uuid import uuid4

import pytest
from flask import Flask
from flask_principal import Identity, Permission, UserNeed

from invenio_records_resources.services import RecordService, \
    RecordServiceConfig
from invenio_records_resources.services.resolver import UUIDResolver


@pytest.fixture()
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))


@pytest.fixture()
def fake_record_db():
    """A fake record."""
    return {
        uuid4(): {'title': 'Fake record'},
    }


@pytest.fixture()
def fake_record_cls(fake_record_db):
    """Fake record class."""
    class FakeRecord(dict):
        @classmethod
        def get_record(cls, id_):
            fake_record = fake_record_db.get(id_)
            if fake_record:
                return cls(fake_record)
            else:
                raise Exception('Record not found')

    return FakeRecord


@pytest.fixture()
def fake_permission_policy_cls():
    """Fake record fixture."""
    class FakePermissionPolicy(Permission):
        def __init__(self, action_name, **kwargs):
            self.needs = set()
            self.excludes = set()

    return FakePermissionPolicy


@pytest.fixture()
def service_config_cls(fake_record_cls, fake_permission_policy_cls):
    """Service configuration class."""
    class TestRecordServiceConfig(RecordServiceConfig):
        record_cls = fake_record_cls
        resolver_cls = UUIDResolver
        permission_policy_cls = fake_permission_policy_cls

    return TestRecordServiceConfig


@pytest.fixture()
def service_cls(service_config_cls):
    """Record service class."""
    class TestRecordService(RecordService):
        default_config = service_config_cls

    return TestRecordService
