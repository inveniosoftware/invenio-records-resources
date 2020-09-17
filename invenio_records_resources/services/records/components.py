# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records service component base classes."""


class ServiceComponent:
    """Base service component."""

    def __init__(self, service, *args, **kwargs):
        """Constructor."""
        self.service = service

    def create(self, identity, **kwargs):
        """Create handler."""
        pass

    def read(self, identity, **kwargs):
        """Read handler."""
        pass

    def update(self, identity, **kwargs):
        """Update handler."""
        pass

    def delete(self, identity, **kwargs):
        """Delete handler."""
        pass

    def search(self, identity, search, params, **kwargs):
        """Search handler."""
        return search


class MetadataComponent(ServiceComponent):
    """Service component for metadata."""

    def create(self, identity, data=None, record=None, **kwargs):
        """Inject parsed metadata to the record."""
        record.metadata = data.get('metadata', {})

    def update(self, identity, data=None, record=None, **kwargs):
        """Inject parsed metadata to the record."""
        record.metadata = data.get('metadata', {})


class PIDSComponent(ServiceComponent):
    """Service component for PIDs integration."""


class FilesComponent(ServiceComponent):
    """Service component for files integration."""


class AccessComponent(ServiceComponent):
    """Service component for access integration."""

    def create(self, identity, data=None, record=None, **kwargs):
        """Add basic ownership fields to the record."""
        validated_data = data.get('access', {})
        # TODO (Alex): replace with `record.access = ...`
        validated_data.setdefault('created_by', identity.id)
        validated_data.setdefault('owners', [identity.id])
        record.update({'access': validated_data})

    def update(self, identity, data=None, record=None, **kwargs):
        """Update handler."""
        validated_data = data.get('access', {})
        # TODO (Alex): replace with `record.access = ...`
        validated_data.pop('created_by', None)
        record.update({'access': validated_data})
