# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files service components."""

from invenio_db import db
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import ObjectVersion

from .base import FileServiceComponent


class FileContentComponent(FileServiceComponent):
    """File metadata service component."""

    def set_file_content(
            self, id, file_key, identity, stream, content_length, record):
        """Set file content handler."""
        # Check if associated file record exists and is not already committed.
        # TODO: raise an appropriate exception
        # TODO: check if stream is not exhausted
        file_record = record.files.get(file_key)
        if file_record is None:
            raise Exception(
                f'File with key "{file_key}" has not been initialized yet.')
        if file_record.file:
            raise Exception(f'File with key "{file_key}" is commited.')

        # Check size limitations
        bucket = record.bucket
        size_limit = bucket.size_limit
        if content_length and size_limit and content_length > size_limit:
            desc = 'File size limit exceeded.' \
                if isinstance(size_limit, int) else size_limit.reason
            raise FileSizeError(description=desc)

        # DB connection?
        # re uploading failed upload?

        with db.session.begin_nested():
            # TODO: in case we want to update a file, this keeps the old
            # FileInstance. It might be better to call ObjectVersion.remove()
            # before or after the "set_content"
            obj = ObjectVersion.create(bucket, file_key)
            obj.set_contents(
                stream, size=content_length, size_limit=size_limit)

    def get_file_content(self, id, file_key, identity, record):
        """Get file content handler."""
        # TODO Signal here or in resource?
        # file_downloaded.send(file_obj)
