# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Data validator tests."""

import pytest
from marshmallow import Schema, fields
from marshmallow.exceptions import ValidationError

from invenio_records_resources.services import DataValidator, \
    MarshmallowDataValidator


def test_data_validator():
    """Tests the data validator interface."""

    validator = DataValidator()

    with pytest.raises(NotImplementedError):
        validator.validate(data=None)


def test_marshmallow_data_validator(input_record):
    """Tests the marshmallow data validator."""

    validator = MarshmallowDataValidator()
    validated_data = validator.validate(data=input_record)

    fields_to_check = input_record.keys()
    validated_data_keys = validated_data.keys()
    for field in fields_to_check:
        assert field in validated_data

    assert len(fields_to_check) == len(validated_data_keys)


def test_marshmallow_data_validator_fail(input_record):
    """Tests the marshmallow data validator with invalid data."""

    validator = MarshmallowDataValidator()
    input_record.pop("title")

    with pytest.raises(ValidationError) as validation_error:
        invalidated_data = validator.validate(data=input_record)

    error_message = validation_error.value.messages

    assert "title" in error_message.keys()


class CustomSchemaJSONV1(Schema):
    """Custom schema class."""

    custom_field = fields.String(required=True)
    extra_field = fields.String()


def test_marshmallow_data_validator_with_custom_schema():
    """Tests the marshmallow data validator."""

    input_record = {"custom_field": "test_value"}

    validator = MarshmallowDataValidator(schema=CustomSchemaJSONV1)
    validated_data = validator.validate(data=input_record)

    assert "custom_field" in validated_data


def test_marshmallow_data_validator_with_custom_schema_partial():
    """Tests the marshmallow data validator."""

    input_record = {"extra_field": "test_value"}

    validator = MarshmallowDataValidator(schema=CustomSchemaJSONV1)
    validated_data = validator.validate(data=input_record, partial=True)

    assert "extra_field" in validated_data
    assert "custom_field" not in validated_data

    with pytest.raises(ValidationError) as validation_error:
        invalidated_data = validator.validate(data=input_record)

    error_message = validation_error.value.messages
    assert "custom_field" in error_message.keys()


def test_marshmallow_data_validator_with_custom_schema_fail(input_record):
    """Tests the marshmallow data validator with invalid data."""

    input_record = {
        "custom_field": "test_value",
        "non_desired_field": "test_value"
    }

    validator = MarshmallowDataValidator(schema=CustomSchemaJSONV1)

    with pytest.raises(ValidationError) as validation_error:
        invalidated_data = validator.validate(data=input_record)

    error_message = validation_error.value.messages

    assert "non_desired_field" in error_message.keys()
