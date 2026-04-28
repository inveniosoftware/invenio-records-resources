# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
# Copyright (C) 2024 Graz University of Technology.
# Copyright (C) 2026 CESNET z.s.p.o.
#
# Invenio-records-resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test invenio-records-resources alembic."""

import pytest
from invenio_db.utils import alembic_test_context, drop_alembic_version_table


def test_alembic(app, db, extra_entry_points):
    """Test alembic recipes."""
    ext = app.extensions["invenio-db"]

    if db.engine.name == "sqlite":
        raise pytest.skip("Upgrades are not supported on SQLite.")

    app.config["ALEMBIC_CONTEXT"] = alembic_test_context()

    # Check that this package's SQLAlchemy models have been properly registered
    tables = [x for x in db.metadata.tables]
    assert "files_location" in tables
    assert "files_bucket" in tables

    def assert_no_unexpected_migrations():
        # names created by RecordTypeFactory in tests and registered to sqlalchemy
        extra_names = [
            "grant_metadata",
            "granttest_metadata",
            "license_metadata",
            "myrecord_metadata",
            "optionalendpoint_metadata",
            "optionalindex_metadata",
            "optionalschemapath_metadata",
            "optionalversion_metadata",
            "recordcls_metadata",
            "resourcetest_metadata",
            "searchfacets_metadata",
            "servicetest_metadata",
        ]
        unexpected_migrations = [
            m
            for m in ext.alembic.compare_metadata()
            if "mock" not in m[1].name.lower() and m[1].name.lower() not in extra_names
        ]
        assert unexpected_migrations == []

    # Check that Alembic agrees that there's no further tables to create.
    assert_no_unexpected_migrations()

    # Drop everything and recreate tables all with Alembic
    db.drop_all()
    drop_alembic_version_table()
    ext.alembic.upgrade()

    assert_no_unexpected_migrations()

    drop_alembic_version_table()
