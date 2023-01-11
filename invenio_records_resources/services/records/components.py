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

from invenio_files_rest.errors import InvalidKeyError
from invenio_i18n import gettext as _
from marshmallow import ValidationError

from ..base.components import BaseServiceComponent
from ..uow import ChangeNotificationOp


class ServiceComponent(BaseServiceComponent):
    """Base service component."""

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


class MetadataComponent(ServiceComponent):
    """Service component for metadata."""

    def create(self, identity, data=None, record=None, errors=None, **kwargs):
        """Inject parsed metadata to the record."""
        record.metadata = data.get("metadata", {})

    def update(self, identity, data=None, record=None, **kwargs):
        """Inject parsed metadata to the record."""
        record.metadata = data.get("metadata", {})


class FilesOptionsComponent(ServiceComponent):
    """Service component for files' options.

    It only deals with:
    - enabled / disabled (metadata-only) files
    - default_preview
    """

    def _validate_files_enabled(self, record, enabled):
        """Validate files enabled."""
        if not enabled and record.files.values():
            raise ValidationError(
                _(
                    "You must first delete all files to set the record to "
                    "be metadata-only."
                ),
                field_name="files.enabled",
            )

    def assign_files_enabled(self, record, enabled):
        """Assign files enabled.

        This is a public interface so that it can be reused elsewhere
        (e.g. drafts-resources).
        """
        self._validate_files_enabled(record, enabled)
        record.files.enabled = enabled

    def assign_files_default_preview(self, record, default_preview):
        """Assign files default_preview."""
        try:
            record.files.default_preview = default_preview
        except InvalidKeyError as e:
            raise ValidationError(
                e.get_description(), field_name="files.default_preview"
            )

    def create(self, identity, data=None, record=None, errors=None, **kwargs):
        """Inject parsed files options in the record."""
        # "enabled" presence is guaranteed by schema
        record.files.enabled = data["files"]["enabled"]

    def update(self, identity, data=None, record=None, **kwargs):
        """Inject parsed files options in the record."""
        # "enabled" presence is guaranteed by schema
        enabled = data["files"]["enabled"]
        self.assign_files_enabled(record, enabled)
        default_preview = data["files"].get("default_preview")
        self.assign_files_default_preview(record, default_preview)


class RelationsComponent(ServiceComponent):
    """Relations service component."""

    def read(self, identity, record=None):
        """Read record handler."""
        record.relations.dereference()


class ChangeNotificationsComponent(ServiceComponent):
    """Back Relations service component."""

    def update(self, identity, data=None, record=None, uow=None, **kwargs):
        """Register a task for the update propagation."""
        # FIXME: until the run_components has been fixed the uow
        # is passed as a cmp attr instead of param.
        self.uow.register(
            ChangeNotificationOp(
                record_type=self.service.id,
                records=[record],
            )
        )
