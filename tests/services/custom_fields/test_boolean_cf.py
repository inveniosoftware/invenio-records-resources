# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test Boolean Custom Field."""

import pytest
from marshmallow import Schema, ValidationError

from invenio_records_resources.services.custom_fields import BooleanCF


def test_booleancf_mapping():
    cf = BooleanCF("name")
    assert cf.mapping == {"type": "boolean"}


def test_booleancf():
    cf = BooleanCF("name", multiple=False)
    schema = Schema.from_dict({"test": cf.field})()

    assert schema.load({"test": True}) == {"test": True}

    # tests "truthy" and "falsy" sets
    assert schema.dump({"test": 1}) == {"test": True}
    assert schema.dump({"test": "true"}) == {"test": True}
    assert schema.dump({"test": "True"}) == {"test": True}
    assert schema.dump({"test": 0}) == {"test": False}
    assert schema.dump({"test": "false"}) == {"test": False}
    assert schema.dump({"test": "False"}) == {"test": False}


def test_booleancf_list():
    cf = BooleanCF("name", multiple=True)
    schema = Schema.from_dict({"test": cf.field})()

    assert schema.load({"test": [True, False]}) == {"test": [True, False]}

    with pytest.raises(ValidationError):
        schema.load({"test": True})
