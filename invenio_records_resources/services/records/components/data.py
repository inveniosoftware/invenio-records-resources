# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records service component base classes."""

from .base import ServiceComponent


class DataComponent(ServiceComponent):
    """Service component which sets all data in the record."""

    def create(self, identity, data=None, record=None, errors=None, **kwargs):
        """Create a new record."""
        record.update(data)

    def update(self, identity, data=None, record=None, **kwargs):
        """Update an existing record."""
        # Clear any top-level field not set in the data.
        # Note: This ensures that if a user removes a top-level key, then we
        # also remove it from the record (since record.update() doesn't take
        # care of this). Removal of subkeys is not an issue as the
        # record.update() will update the top-level key.
        fields = set(self.service.config.schema().fields.keys())
        data_fields = set(data.keys())
        for f in fields - data_fields:
            if f in record:
                del record[f]
        # Update the remaining keys.
        record.update(data)
        # Clear None values from the record.
        record.clear_none()
