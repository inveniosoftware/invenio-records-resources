# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-License-Identifier: MIT

"""Custom Fields schema for InvenioRDM."""

from flask import current_app
from marshmallow import Schema


class CustomFieldsSchema(Schema):
    """Marshmallow schema for custom fields.

    Loads all schemas from the configured fields.
    """

    field_property_name = "field"

    def __init__(self, fields_var, *args, **kwargs):
        """constructor."""
        super().__init__(*args, **kwargs)
        config = current_app.config.get(fields_var, [])
        self.fields = {
            field.name: getattr(field, self.field_property_name) for field in config
        }
        self._schema = Schema.from_dict(self.fields)()

    def _serialize(self, obj, **kwargs):
        """Dumps the custom fields values."""
        return self._schema.dump(obj)

    def _deserialize(self, data, **kwargs):
        """Loads the custom fields values."""
        return self._schema.load(data=data)

    class Meta:
        # configuration for deep fried marshmallow, ignored if deepfriedmarshmallow is not installed
        # needs to be present in order to serialize systemfields correctly
        jit_options = {"expected_serialize_type": "hybrid"}


class CustomFieldsSchemaUI(CustomFieldsSchema):
    """Marshmallow schema for custom fields in the UI."""

    field_property_name = "ui_field"
