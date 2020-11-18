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
from ..records.schema import MarshmallowServiceSchema
from .config import RecordFileServiceConfig

# FIXME: Remove when there is a proper file
dummy_file_entry = {
    "created": "2020-11-15T19:04:22",
    "updated": "2020-11-15T19:04:22",
    "key": "article.pdf",
    "checksum": "md5:abcdef...",
    "size": 2048,
    "metadata": {
        "description": "Published article PDF.",
    },
    "links": {
        "upload": {
            "href": "/api/records/jnmmp-51n47/files/article.pdf/content",
            "method": "PUT"
        },
        "self": "/api/records/jnmmp-51n47/files/article.pdf",
    }
}


# FIXME: Two functions and one property have to be prefixed `file_` to avoid
#        collisions when using the mixing e.g. along with a RecordService.
class FileServiceMixin(Service):
    """File service mixin.

    This service is meant to work as a mixin, along a service that
    supports records. It is not meant to work as an standalone service.
    """

    default_config = None  # It is defined when the mixin is used.

    @property
    def file_schema(self):
        """Returns the data schema instance."""
        return MarshmallowServiceSchema(self, schema=self.config.file_schema)

    def file_result_item(self, *args, **kwargs):
        """Create a new instance of the resource unit.

        A resource unit is an instantiated object representing one unit
        of a Resource. It is what a Resource transacts in and therefore
        what a Service must provide.
        """
        return self.config.file_result_item_cls(*args, **kwargs)

    def file_result_list(self, *args, **kwargs):
        """Create a new instance of the resource list.

        A resource list is an instantiated object representing a grouping
        of Resource units. Sometimes this group has additional data making
        a simple iterable of resource units inappropriate. It is what a
        Resource list methods transact in and therefore what
        a Service must provide.
        """
        return self.config.file_result_list_cls(*args, **kwargs)
    #
    # High-level API
    #

    def list_files(self, id_, identity):
        """List the files of a record."""
        return self.file_result_list()

    def init_file(self, id_, identity, data):
        """Initialize the file upload for the record."""
        return self.file_result_item()

    def delete_all_files(self, id_, identity):
        """Delete all the files of the record.."""
        return True

    def update_file_metadata(self, id_, file_id, identity, data):
        """Update the metadata of a file."""
        return self.file_result_item()

    def read_file_metadata(self, id_, file_id, identity):
        """Read the metadata of a file."""
        return self.file_result_item()

    def commit_file(self, id_, file_id, identity, links_config):
        """Commit a file upload."""
        return self.file_result_item()

    def delete_file(self, id_, file_id, identity, revision_id):
        """Delete a single file."""
        return True

    def save_file(self, id_, file_id, identity, content, links_config):
        """Save file content."""
        return self.file_result_item()

    def retrieve_file(self, id_, file_id, identity, links_config):
        """Retrieve file content."""
        return {}


class RecordFileService(RecordService, FileServiceMixin):
    """Record service with files support."""

    default_config = RecordFileServiceConfig
