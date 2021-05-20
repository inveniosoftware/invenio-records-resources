# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files metadata component components."""

from copy import deepcopy

from invenio_files_rest.models import ObjectVersion

from .base import FileServiceComponent


class FileMetadataComponent(FileServiceComponent):
    """File metadata service component."""

    def init_files(self, id, identity, record, data):
        """Init files handler."""
        # TODO: Load via marshmallow schema?
        for file_metadata in data:
            temporary_obj = deepcopy(file_metadata)
            record.files.create(temporary_obj.pop('key'), data=temporary_obj)

    def update_file_metadata(self, id, file_key, identity, record, data):
        """Update file metadata handler."""
        record.files.update(file_key, data=data)

    # TODO: `commit_file` might vary based on your storage backend (e.g. S3)
    def commit_file(self, id, file_key, identity, record):
        """Commit file handler."""
        # TODO: Add other checks here (e.g. verify checksum, S3 upload)
        file_obj = ObjectVersion.get(record.bucket.id, file_key)
        if not file_obj:
            raise Exception(f'File with key {file_key} not uploaded yet.')
        record.files[file_key] = file_obj
