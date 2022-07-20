# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields sub service for InvenioRDM."""

from flask import current_app
from elasticsearch.exceptions import RequestError
from invenio_drafts_resources.services.records import RecordService, RecordServiceConfig

from .schema import CustomFieldsSchema


class CustomFieldsServiceConfig(RecordServiceConfig):
    """Configuration for the Custom Fields service."""

    fields_config_var = None
    schema_parent = None
    schema = CustomFieldsSchema


class CustomFieldsService(RecordService):
    """Custom Fields service."""

    def create(self, fields_name):
        """Create custom fields."""

        fields = []
        available_fields = current_app.config.get(
            self.config.fields_config_var, {}
        )

        if fields_name:
            for field_name in fields_name:
                fields.append(available_fields.get(field_name))
        else:
            fields = available_fields.values()

        # this means we do not have to choose a write index
        # we update only the latest mapping/alias
        index = self.record_cls.index

        properties = {}
        for field in fields:
            properties[f"custom.{field.name}"] = field.mapping

        try:
            res = index.put_mapping(body={"properties": properties})
        except RequestError as e:
            return False, e.info["error"]["reason"]

        return res.get("acknowledged"), None

    def exists(self, field_name):
        """Check if a custom field exists."""
        index = self.record_cls.index

        mapping = list(index.get_mapping().values())[0]["mappings"]

        parts = field_name.split(".")
        for part in parts:
            mapping = mapping["properties"]  # here to avoid last field access
            if part not in mapping.keys():
                return False

            mapping = mapping[part]

        return True
