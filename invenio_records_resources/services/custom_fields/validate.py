# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from .errors import CustomFieldsNotConfigured, InvalidCustomFieldsNamespace


def validate_custom_fields(available_fields, namespaces=None, given_fields=None):
    """Validate custom fields."""
    to_validate = []
    if not given_fields:
        to_validate = available_fields
    else:
        given_fields = set(given_fields)
        found = set()
        for field in available_fields:
            if field.name in given_fields:
                found.add(field.name)
                to_validate.append(field)

        not_found = given_fields - found
        if not_found:
            raise CustomFieldsNotConfigured(not_found)

    for field in to_validate:
        parts = field.name.split(":")
        is_namespaced = len(parts) > 1
        invalid_namespace = len(parts) > 2
        configured_namespace = parts[0] in namespaces

        if is_namespaced and (invalid_namespace or not configured_namespace):
            raise InvalidCustomFieldsNamespace(field.name, parts[0])
