# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET z.s.p.o.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""S3 testing configuration."""
import os

import pytest

from tests.mock_module.api import RecordWithFiles


#
# Need to redefine the app_config fixture to include the S3 configuration
# and remove the default file-based storage.
#
@pytest.fixture(scope="module")
def app_config(app_config):
    """Override pytest-invenio app_config fixture.

    Needed to set up S3 configuration.
    """
    app_config["RECORDS_RESOURCES_FILES_ALLOWED_DOMAINS"] = [
        "inveniordm.test",
    ]
    app_config["RECORDS_RESOURCES_FILES_ALLOWED_REMOTE_DOMAINS"] = [
        "inveniordm.test",
    ]
    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "S": "Standard",
    }

    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "S"

    app_config["RECORDS_REFRESOLVER_CLS"] = (
        "invenio_records.resolver.InvenioRefResolver"
    )
    app_config["RECORDS_REFRESOLVER_STORE"] = (
        "invenio_jsonschemas.proxies.current_refresolver_store"
    )
    app_config["FILES_REST_STORAGE_FACTORY"] = "invenio_s3.s3fs_storage_factory"

    # s3 configuration
    app_config["S3_ENDPOINT_URL"] = os.environ["S3_ENDPOINT_URL"]
    app_config["S3_ACCESS_KEY_ID"] = os.environ["S3_ACCESS_KEY_ID"]
    app_config["S3_SECRET_ACCESS_KEY"] = os.environ["S3_SECRET_ACCESS_KEY"]

    return app_config


@pytest.fixture()
def s3_location(app, db):
    """Creates an s3 location for a test."""
    from invenio_files_rest.models import Location

    location_obj = Location(name="pytest-s3-location", uri="s3://default", default=True)

    db.session.add(location_obj)
    db.session.commit()

    yield location_obj


@pytest.fixture()
def example_s3_file_record(db, input_data, s3_location):
    """Example record."""
    record = RecordWithFiles.create({}, **input_data)
    record.commit()
    db.session.commit()
    return record
