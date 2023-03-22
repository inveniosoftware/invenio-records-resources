# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test Text and Keyword Custom Field."""

import pytest
from marshmallow import Schema, ValidationError
from marshmallow_utils.fields import SanitizedHTML

from invenio_records_resources.services.custom_fields import KeywordCF, TextCF

#
# KeywordCF
#


def test_keywordcf_mapping():
    cf = KeywordCF("name")
    assert cf.mapping == {"type": "keyword"}


def test_keywordcf_required():
    cf = KeywordCF("name", field_args={"required": True})
    schema = Schema.from_dict({"test": cf.field})()

    schema.load({"test": "a string"})

    with pytest.raises(ValidationError):
        schema.load({})


def test_keywordcf_validate():
    def at_least_3_chars(value):
        if len(value) < 3:
            raise ValidationError("Must be at least 3 characters")

    cf = KeywordCF("name", field_args={"validate": at_least_3_chars})
    schema = Schema.from_dict({"test": cf.field})()

    schema.load({"test": "a string"})

    with pytest.raises(ValidationError) as e:
        schema.load({"test": "ab"})

    errors = e.value.messages
    assert len(errors) == 1
    assert errors["test"] == ["Must be at least 3 characters"]


def test_keywordcf_error_messages():
    cf = KeywordCF(
        "name",
        field_args={
            "required": True,
            "error_messages": {"required": "Custom error"},
        },
    )
    schema = Schema.from_dict({"test": cf.field})()

    with pytest.raises(ValidationError) as e:
        schema.load({})

    errors = e.value.messages
    assert len(errors) == 1
    assert errors["test"] == ["Custom error"]


def test_keywordcf_custom_field_cls_list():
    cf = KeywordCF("name", field_cls=SanitizedHTML, multiple=True)
    schema = Schema.from_dict({"test": cf.field})()

    assert schema.load(
        {"test": ["<p>a string</p>", "<span>another string</span>"]}
    ) == {"test": ["<p>a string</p>", "<span>another string</span>"]}

    with pytest.raises(ValidationError):
        schema.load({"test": "a string"})


#
# TextCF
#


def test_textcf_mapping():
    cf = TextCF("name")
    assert cf.mapping == {"type": "text"}

    cf = TextCF("name", use_as_filter=True)
    assert cf.mapping == {"type": "text", "fields": {"keyword": {"type": "keyword"}}}


def test_textcf_list():
    cf = TextCF("name", multiple=True)
    schema = Schema.from_dict({"test": cf.field})()

    assert schema.load({"test": ["a string", "another string"]}) == {
        "test": ["a string", "another string"]
    }

    with pytest.raises(ValidationError):
        schema.load({"test": "a string"})


def test_textcf_custom_field_cls_list():
    cf = TextCF("name", field_cls=SanitizedHTML, multiple=True)
    schema = Schema.from_dict({"test": cf.field})()

    assert schema.load(
        {"test": ["<p>a string</p>", "<span>another string</span>"]}
    ) == {"test": ["<p>a string</p>", "<span>another string</span>"]}

    with pytest.raises(ValidationError):
        schema.load({"test": "a string"})
