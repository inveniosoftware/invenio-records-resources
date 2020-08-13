# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Data validation API."""

from ..schemas import MetadataSchemaJSONV1


class DataValidator:
    """Data validator interface."""

    def validate(self, data, *args, **kwargs):
        """Validate data."""
        raise NotImplementedError()


class MarshmallowDataValidator:
    """Data validator based on a Marshamllow schema."""

    def __init__(self, schema=MetadataSchemaJSONV1, *args, **kwargs):
        """Constructor."""
        self.schema = schema

    def validate(self, data, partial=False, context=None):
        """Validate by dumping it on the marshmallow schema.

        :params partial: If true validation will only be performed on existing
        fields. Meaning, required fields can be missing.
        :returns: The validated data as a dict.
        """
        return self.schema(context=context).load(data, partial=partial)
