# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files field tests."""

from copy import deepcopy

import pytest

from invenio_records_resources.records.dumpers import CustomFieldsDumperExt
from invenio_records_resources.services.custom_fields import (
    EDTFDateStringCF,
    ISODateStringCF,
    KeywordCF,
    TextCF,
)
from tests.mock_module.api import Record


@pytest.fixture(scope="module")
def app_config(app_config):
    """Override pytest-invenio app_config fixture.

    Needed to set the fields on the custom fields schema.
    """
    app_config["RECORDS_RESOURCES_CUSTOM_CONFIG"] = [
        TextCF(name="text"),
        KeywordCF(name="keyword"),
        EDTFDateStringCF(name="edtf"),
        ISODateStringCF(name="iso"),
    ]

    return app_config


@pytest.fixture()
def record_with_cfs(app):
    return Record.create(
        {
            "metadata": {"title": "test"},
            "custom_fields": {
                "text": "text",
                "keyword": "keyword",
                "edtf": "2021",
                "iso": "2021-01-01",
            },
        }
    )


def test_custom_field_dumperext(record_with_cfs):
    """Test dump."""
    dumper = CustomFieldsDumperExt("RECORDS_RESOURCES_CUSTOM_CONFIG")
    expected_load_data = deepcopy(record_with_cfs["custom_fields"])
    # dump
    dumper.dump(record=None, data=record_with_cfs)
    expected_dump_data = {
        "text": "text",
        "keyword": "keyword",
        "edtf": {
            "date": "2021",
            "date_range": {"gte": "2021-01-01", "lte": "2021-12-31"},
        },
        "iso": "2021-01-01",
    }

    assert record_with_cfs["custom_fields"] == expected_dump_data
    # load
    dumper.load(data=record_with_cfs, record_cls=None)
    assert record_with_cfs["custom_fields"] == expected_load_data
