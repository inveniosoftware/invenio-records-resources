# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files service components."""

from ...base.components import BaseServiceComponent


class FileServiceComponent(BaseServiceComponent):
    """Base service component."""

    def list_files(self, identity, id_, record):
        """List files handler."""
        pass

    def init_files(self, identity, id_, record, data):
        """Init files handler."""
        pass

    def update_file_metadata(self, identity, id_, file_key, record, data):
        """Update file metadata handler."""
        pass

    def read_file_metadata(self, identity, id_, file_key, record):
        """Read file metadata."""
        pass

    def extract_file_metadata(self, identity, id_, file_key, record, file_record):
        """Extract file metadata handler."""

    def commit_file(self, identity, id_, file_key, record):
        """Commit file handler."""
        pass

    def delete_file(self, identity, id_, file_key, record, deleted_file):
        """Delete file handler."""
        pass

    def delete_all_file(self, id_, file_key, identity, record, results):
        """Delete all files handler."""
        pass

    def set_file_content(self, identity, id_, file_key, stream, content_length, record):
        """Set file content handler."""
        pass

    def get_file_content(self, identity, id_, file_key, record):
        """Get file content handler."""
        pass
