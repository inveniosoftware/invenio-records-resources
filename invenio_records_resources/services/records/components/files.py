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

from .base import ServiceComponent, BaseRecordFilesComponent


class BaseFilesOptionsComponent(BaseRecordFilesComponent, ServiceComponent):
    """Service component for files' options.

    It only deals with:
    - enabled / disabled (metadata-only) files
    - default_preview
    """

    def _validate_files_enabled(self, record, enabled):
        """Validate files enabled."""
        record_files = self.get_record_files(record)
        if not enabled and record_files.values():
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
        record_files = self.get_record_files(record)
        self._validate_files_enabled(record, enabled)
        record_files.enabled = enabled

    def assign_files_default_preview(self, record, default_preview):
        """Assign files default_preview."""
        record_files = self.get_record_files(record)
        try:
            record_files.default_preview = default_preview
        except InvalidKeyError as e:
            raise ValidationError(
                e.get_description(), field_name="files.default_preview"
            )

    def create(self, identity, data=None, record=None, errors=None, **kwargs):
        """Inject parsed files options in the record."""
        # "enabled" presence is guaranteed by schema
        record_files = self.get_record_files(record)
        record_files.enabled = data["files"]["enabled"]

    def update(self, identity, data=None, record=None, **kwargs):
        """Inject parsed files options in the record."""
        # "enabled" presence is guaranteed by schema

        enabled = data[self.files_data_key]["enabled"]
        self.assign_files_enabled(record, enabled)
        default_preview = data[self.files_data_key].get("default_preview")
        self.assign_files_default_preview(record, default_preview)


class FilesOptionsComponent(BaseFilesOptionsComponent):
    _files_attr_key = "files"
    _files_data_key = "files"
    _files_bucket_attr_key = "bucket"
    _files_bucket_id_attr_key = "bucket_id"


class AuxFilesOptionsComponent(BaseFilesOptionsComponent):
    _files_attr_key = "aux_files"
    _files_data_key = "aux_files"
    _files_bucket_attr_key = "aux_bucket"
    _files_bucket_id_attr_key = "aux_bucket_id"
