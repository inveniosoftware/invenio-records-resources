# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records dumpers and extensions."""

from copy import deepcopy

from flask import current_app
from invenio_records.dumpers import Dumper, SearchDumperExt

from .api import File


class CustomFieldsDumperExt(SearchDumperExt):
    """Custom fields dumper extension."""

    def __init__(self, fields_var, key="custom_fields"):
        """Initialize the dumper.

        :param key: The dictionary key where custom fields are set.
        """
        self._fields_var = fields_var
        self.key = key

    def dump(self, record, data):
        """Dump custom fields."""
        custom_fields = current_app.config.get(self._fields_var, {})

        for cf in custom_fields:
            cf.dump(data, cf_key=self.key)

    def load(self, data, record_cls):
        """Load custom fields."""
        custom_fields = current_app.config.get(self._fields_var, {})

        for cf in custom_fields:
            cf.load(data, cf_key=self.key)


class PartialFileDumper(Dumper):
    """File in record dumper."""

    def dump(self, record, data):
        """Dump a partial file record to include into another record."""
        data = {
            "uuid": str(record.id),
            "version_id": record.revision_id + 1,
            "metadata": deepcopy(dict(record.get("metadata", {}))),
            "key": record.key,
        }
        if record.file:
            data.update(record.file.dumps())
        return data

    def load(self, data, record_cls):
        """Load a record from the source document of a search engine hit."""
        model_data = {
            "id": str(data["uuid"]),
            "version_id": data["version_id"],
            "key": data["key"],
            "record_id": data["record_id"],
            "object_version_id": data["object_version_id"],
        }
        record_data = {"metadata": data["metadata"]}
        model = record_cls.model_cls(**model_data)
        record = record_cls(record_data, model=model)
        f = File.from_dump(data)
        record.object_version = f.object_model
        return record
