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
from copy import deepcopy
from datetime import date

import pytest
from flask import Flask
from invenio_app.factory import create_app as _create_app

from invenio_records_resources.resources import RecordResource


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return _create_app


# FIXME: this two should come from `invenio-rdm-records`
# However, this module should not be RDM dependent
@pytest.fixture(scope="function")
def minimal_input_record():
    """Minimal record data as dict coming from the external world."""
    return {
        "_access": {"metadata_restricted": False, "files_restricted": False},
        "_owners": [1],
        "_created_by": 1,
        "access_right": "open",
        "resource_type": {"type": "image", "subtype": "image-photo"},
        # Technically not required
        "creators": [],
        "titles": [
            {"title": "A Romans story", "type": "Other", "lang": "eng"}
        ],
    }


@pytest.fixture(scope="function")
def minimal_record(minimal_input_record):
    """Dictionary with the minimum required fields to create a record.

    It fills in the missing and post_loaded fields.
    """
    record = deepcopy(minimal_input_record)
    record["publication_date"] = date.today().isoformat()
    record["_publication_date_search"] = date.today().isoformat()
    return record
