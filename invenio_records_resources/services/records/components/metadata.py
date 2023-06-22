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


class MetadataComponent(ServiceComponent):
    """Service component for metadata."""

    def create(self, identity, data=None, record=None, errors=None, **kwargs):
        """Inject parsed metadata to the record."""
        record.metadata = data.get("metadata", {})

    def update(self, identity, data=None, record=None, **kwargs):
        """Inject parsed metadata to the record."""
        record.metadata = data.get("metadata", {})
