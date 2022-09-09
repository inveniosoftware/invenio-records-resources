# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test ISODate and EDTF Custom Field."""

import pytest
from marshmallow import Schema, ValidationError

from invenio_records_resources.services.custom_fields import (
    EDTFDateStringCF,
    ISODateStringCF,
)


#
# ISODateCF
#
def test_isodatestring_mapping():
    cf = ISODateStringCF("name")
    assert cf.mapping == {"type": "date"}


def test_isodatestring_validate():
    cf = ISODateStringCF("name")
    schema = Schema.from_dict({"test": cf.field})()

    assert schema.load({"test": "1999-10-27"}) == {"test": "1999-10-27"}
    pytest.raises(ValidationError, schema.load, {"f": "2020/2021"})


#
# EDTFDateStringCF
#
def test_edtfdatestring_mapping():
    cf = EDTFDateStringCF("name")
    assert cf.mapping == {
        "type": "object",
        "properties": {
            "date": {"type": "keyword"},
            "date_range": {"type": "date_range"},
        },
    }


def test_edtfdatestring_validate():
    cf = EDTFDateStringCF("name")
    schema = Schema.from_dict({"test": cf.field})()

    assert schema.load({"test": "2020-09/2020-10"}) == {"test": "2020-09/2020-10"}

    pytest.raises(ValidationError, schema.load, {"test": "2020-09-21garbage"})
    # Not chronological
    pytest.raises(ValidationError, schema.load, {"test": "2021/2020"})
    # Not date or interval
    pytest.raises(ValidationError, schema.load, {"test": "2020-01-01T10:00:00"})
