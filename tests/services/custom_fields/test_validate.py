# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test Custom Fields validation."""

import pytest

from invenio_records_resources.services.custom_fields import TextCF
from invenio_records_resources.services.custom_fields.errors import (
    CustomFieldsNotConfigured,
    InvalidCustomFieldsNamespace,
)
from invenio_records_resources.services.custom_fields.validate import (
    validate_custom_fields,
)


def test_validate_custom_fields():
    available = [TextCF(name="text")]
    validate_custom_fields(available, namespaces=set())
    validate_custom_fields(available, given_fields=["text"], namespaces=set())

    pytest.raises(
        CustomFieldsNotConfigured,
        validate_custom_fields,
        available,
        given_fields=["invalid"],
        namespaces=set(),
    )


def test_validate_custom_fields_namespaces():
    available = [TextCF(name="text"), TextCF(name="ns:text")]
    validate_custom_fields(available, namespaces={"ns"})
    validate_custom_fields(available, given_fields=["text"], namespaces={"ns"})
    validate_custom_fields(available, given_fields=["ns:text"], namespaces={"ns"})

    pytest.raises(
        InvalidCustomFieldsNamespace,
        validate_custom_fields,
        available_fields=[TextCF(name="invalid:text")],
        namespaces={"ns"},
    )

    pytest.raises(
        InvalidCustomFieldsNamespace,
        validate_custom_fields,
        available_fields=[TextCF(name="invalid:text")],
        given_fields=["invalid:text"],
        namespaces={"ns"},
    )
