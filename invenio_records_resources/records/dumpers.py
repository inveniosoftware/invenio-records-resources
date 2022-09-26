# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records dumpers and extensions."""

from flask import current_app
from invenio_records.dumpers import SearchDumperExt


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
