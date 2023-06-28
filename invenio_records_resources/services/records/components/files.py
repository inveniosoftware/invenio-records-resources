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

from invenio_records_resources.services.base.config import _make_cls

from .base import ServiceComponent


class FileConfigMixin:
    """Mixin class adding dynamic file loading."""

    _files_attr_key = None
    _files_data_key = None
    _files_bucket_attr_key = None
    _files_bucket_id_attr_key = None

    @property
    def files_attr_key(self):
        """Returns files attribute (field) key."""
        return self._files_attr_key

    @property
    def files_data_key(self):
        """Returns files data (field) key."""
        return self._files_data_key or self._files_attr_key

    @property
    def files_bucket_attr_key(self):
        """Returns files bucket (field) key."""
        return self._files_bucket_attr_key

    @property
    def files_bucket_id_attr_key(self):
        """Returns files bucket_id (field) key."""
        return self._files_bucket_id_attr_key

    def get_record_files(self, record):
        """Get files field value of a given record."""
        return getattr(record, self.files_attr_key)

    def get_record_bucket(self, record):
        """Get files bucket of a given record."""
        return getattr(record, self._files_bucket_attr_key)

    def get_record_bucket_id(self, record):
        """Get files bucket id of a given record."""
        return getattr(record, self._files_bucket_attr_key)


class BaseRecordFilesComponent(FileConfigMixin, ServiceComponent):
    """Service component for files' options.

    It only deals with:
    - enabled / disabled (metadata-only) files
    - default_preview
    """

    def __init__(self, service):
        """Initialize the file config mixin."""
        # We assert that attributes are initialized because we cannot
        # pass the atrributes via the constructor due to the limitation
        # of component registration
        assert self._files_attr_key is not None
        assert self._files_data_key is not None
        assert self._files_bucket_attr_key is not None
        assert self._files_bucket_id_attr_key is not None

        super().__init__(service)

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
                e.get_description(), field_name=f"{self.files_data_key}.default_preview"
            )

    def create(self, identity, data=None, record=None, errors=None, **kwargs):
        """Inject parsed files options in the record."""
        # "enabled" presence is guaranteed by schema
        record_files = self.get_record_files(record)
        record_files.enabled = data[self.files_data_key]["enabled"]

    def update(self, identity, data=None, record=None, **kwargs):
        """Inject parsed files options in the record."""
        # "enabled" presence is guaranteed by schema

        enabled = data[self.files_data_key]["enabled"]
        self.assign_files_enabled(record, enabled)
        default_preview = data[self.files_data_key].get("default_preview")
        self.assign_files_default_preview(record, default_preview)


FilesAttrConfig = {
    "_files_attr_key": "files",
    "_files_data_key": "files",
    "_files_bucket_attr_key": "bucket",
    "_files_bucket_id_attr_key": "bucket_id",
}

FilesComponent = _make_cls(BaseRecordFilesComponent, {**FilesAttrConfig})
