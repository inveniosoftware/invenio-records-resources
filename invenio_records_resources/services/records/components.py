# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records service component base classes."""

from flask_babelex import gettext as _
from marshmallow import ValidationError


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


class DataComponent(ServiceComponent):
    """Service component which sets all data in the record."""

    def create(self, identity, data=None, record=None, **kwargs):
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


class MetadataComponent(ServiceComponent):
    """Service component for metadata."""

    def create(self, identity, data=None, record=None, **kwargs):
        """Inject parsed metadata to the record."""
        record.metadata = data.get('metadata', {})

    def update(self, identity, data=None, record=None, **kwargs):
        """Inject parsed metadata to the record."""
        record.metadata = data.get('metadata', {})


class FilesOptionsComponent(ServiceComponent):
    """Service component for files' options.

    It only deals with enabled / disabled (metadata-only) files for now.
    """

    def _validate_files_enabled(self, record, enabled):
        """Validate files enabled."""
        if not enabled:
            if record.files.values():
                raise ValidationError(
                    _("You must first delete all files to set the record to "
                      "be metadata-only."),
                    field_name="files.enabled"
                )

    def assign_files_enabled(self, identity, enabled, record=None, **kwargs):
        """Assign files enabled.

        This is a public interface so that it can be reused elsewhere
        (e.g. drafts-resources).
        """
        self._validate_files_enabled(record, enabled)
        record.files.enabled = enabled

    def create(self, identity, data=None, record=None, **kwargs):
        """Inject parsed files options in the record."""
        # presence is guaranteed by schema
        enabled = data["files"]["enabled"]
        self.assign_files_enabled(identity, enabled, record, **kwargs)

    def update(self, identity, data=None, record=None, **kwargs):
        """Inject parsed files options in the record."""
        # presence is guaranteed by schema
        enabled = data["files"]["enabled"]
        self.assign_files_enabled(identity, enabled, record, **kwargs)
