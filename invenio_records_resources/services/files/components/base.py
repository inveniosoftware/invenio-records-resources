# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files service components."""


class FileServiceComponent:
    """Base service component."""

    def __init__(self, service, *args, **kwargs):
        """Constructor."""
        self.service = service

    def list_files(self, id_, identity, record):
        """List files handler."""
        pass

    def init_files(self, id_, identity, record, data):
        """Init files handler."""
        pass

    def post_init_files(self, id_, identity, record, data):
        """Post init files handler."""
        pass

    def update_file_metadata(self, id_, file_key, identity, record, data):
        """Update file metadata handler."""
        pass

    def post_update_file_metadata(self, id_, file_key, identity, record, data):
        """Post update file metadata handler."""
        pass

    def read_file_metadata(self, id_, file_key, identity, record):
        """Read file metadata."""
        pass

    def extract_file_metadata(
            self, id_, file_key, identity, record, file_record):
        """Extract file metadata handler."""

    def commit_file(self, id_, file_key, identity, record):
        """Commit file handler."""
        pass

    def post_commit_file(self, id_, file_key, identity, record):
        """Post commit file handler."""
        pass

    def delete_file(self, id_, file_key, identity, record, deleted_file):
        """Delete file handler."""
        pass

    def post_delete_file(self, id_, file_key, identity, record, deleted_file):
        """Post delete file handler."""
        pass

    def delete_all_file(self, id_, file_key, identity, record, results):
        """Delete all files handler."""
        pass

    def post_delete_all_file(self, id_, file_key, identity, record, results):
        """Post delete all files handler."""
        pass

    def set_file_content(
            self, id_, file_key, identity, stream, content_length, record):
        """Set file content handler."""
        pass

    def post_set_file_content(
            self, id_, file_key, identity, stream, content_length, record):
        """Post set file content handler."""
        pass

    def get_file_content(self, id_, file_key, identity, record):
        """Get file content handler."""
        pass
