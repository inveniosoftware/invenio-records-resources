# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from ..base import Service
from ..records import RecordService
from .config import RecordFileServiceConfig


class FileServiceMixin(Service):
    """File service mixin.

    This service is meant to work as a mixin, along a service that
    supports records. It is not meant to work as an standalone service.
    """

    default_config = None  # It is defined when the mixin is used.

    #
    # High-level API
    #

    def list_files(self, id_, identity):
        """List the files of a record."""
        return {}

    def init_file_upload(self, id_, identity):
        """Initialize the file upload for the record."""
        return {}

    def delete_all_files(self, id_, identity):
        """Delete all the files of the record.."""
        return {}

    def update_file_metadata(self, id_, file_id, identity, data):
        """Update the metadata of a file."""
        return {}

    def read_file_metadata(self, id_, file_id, identity):
        """Read the metadata of a file."""
        return {}

    def commit_file(self, id_, file_id, identity, links_config):
        """Commit a file upload."""
        return {}

    def delete_file(self, id_, file_id, identity, revision_id):
        """Delete a single file."""
        return {}

    def save_file(self, id_, file_id, identity, content, links_config):
        """Save file content."""
        return {}

    def retrieve_file(self, id_, file_id, identity, links_config):
        """Retrieve file content."""
        return {}


class RecordFileService(RecordService, FileServiceMixin):
    """Record service with files support."""

    default_config = RecordFileServiceConfig
