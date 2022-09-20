# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test Integer and Double Custom Field."""

import pytest
from marshmallow import Schema, ValidationError

from invenio_records_resources.services.custom_fields import DoubleCF, IntegerCF

#
# Integer
#


def test_integercf_mapping():
    cf = IntegerCF("name")
    assert cf.mapping == {"type": "integer"}


def test_integercf():
    cf = IntegerCF("name", multiple=False)
    schema = Schema.from_dict({"test": cf.field})()

    assert schema.load({"test": 1}) == {"test": 1}

    with pytest.raises(ValidationError):
        schema.load({"test": 1.1})

    with pytest.raises(ValidationError):
        schema.load({"test": "1"})


#
# Double
#


def test_doublecf_mapping():
    cf = DoubleCF("name")
    assert cf.mapping == {"type": "double"}


def test_doublecf():
    cf = DoubleCF("name", multiple=False)
    schema = Schema.from_dict({"test": cf.field})()

    assert schema.load({"test": 1}) == {"test": 1}
    assert schema.load({"test": 1.1}) == {"test": 1.1}
    # test string acceptance but dumped as double
    assert schema.dump({"test": "1.1"}) == {"test": 1.1}
