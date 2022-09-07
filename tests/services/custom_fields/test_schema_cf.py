# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test Base Custom Field."""

import pytest
from marshmallow import ValidationError

from invenio_records_resources.services.custom_fields import (
    CustomFieldsSchema,
    KeywordCF,
    TextCF,
)


@pytest.fixture(scope="module")
def app_config(app_config):
    """Override pytest-invenio app_config fixture.

    Needed to set the fields on the custom fields schema.
    """
    app_config["RECORDS_RESOURCES_CUSTOM_CONFIG"] = [
        TextCF(name="myorg:txt"),
        TextCF(name="req", field_args={"required": True}),
        TextCF(name="myorg:txt_multiple", multiple=True),
        KeywordCF(name="myorg:keyword_multiple", multiple=True),
    ]

    return app_config


def test_cf_schema(app):
    schema = CustomFieldsSchema("RECORDS_RESOURCES_CUSTOM_CONFIG")
    assert schema.load(
        {
            "myorg:txt": "some",
            "req": "other",
            "myorg:txt_multiple": ["some", "another"],
            "myorg:keyword_multiple": ["some", "another"],
        }
    ) == {
        "myorg:txt": "some",
        "req": "other",
        "myorg:txt_multiple": ["some", "another"],
        "myorg:keyword_multiple": ["some", "another"],
    }

    with pytest.raises(ValidationError):
        assert schema.load({"myorg:txt": "some"})
