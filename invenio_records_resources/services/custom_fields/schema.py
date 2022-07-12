# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields sub service for InvenioRDM."""

from flask import current_app
from marshmallow import Schema


class CustomFieldsSchema(Schema):
    """Marshmallow schema for custom fields.

    Loads all schemas from the configured fields.
    Uses the singleton pattern to avoid loading multiple times.
    """

    # FIXME: config_var better name? somehow link to service config?
    # they are still used independently (e.g. schema in rdm-records)
    def __init__(self, config_var, *args, **kwargs):
        """constructor."""
        super().__init__(*args, **kwargs)
        config = current_app.config.get(config_var, {})
        self.fields = {
            field_key: field.schema() for field_key, field in config.items()
        }
        self._schema = Schema.from_dict(self.fields)()

    def _serialize(self, obj, **kwargs):
        """Dumps the custom fields values."""
        return self._schema.dump(obj)

    def _deserialize(self, data, **kwargs):
        """Loads the custom fields values."""
        return self._schema.load(data=data)
