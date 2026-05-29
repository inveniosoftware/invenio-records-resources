# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""
Implementation of additional storage backends.
"""

import requests
from invenio_files_rest.storage import FileStorage


class RemoteFileStorage(FileStorage):
    """Remote storage backend. This backend is used for storing files
    in a remote location (such as a different web server) and invenio
    does not manage the storage directly (and has no control over it).
    """

    def __init__(self, fileurl, size=None, modified=None):
        """Storage initialization."""
        self.fileurl = fileurl
        super().__init__(size=size, modified=modified)

    def open(self, mode="rb"):
        """Open file.

        The caller is responsible for closing the file.
        """
        if mode != "rb":
            raise NotImplementedError("Only read binary mode is supported.")
        return requests.get(self.fileurl, stream=True).raw

    def delete(self):
        """Delete a file.

        This is a no-op for remote storage as we do not own the storage."""
        return False

    def initialize(self, size=0):
        """Initialize file on storage and truncate to given size."""
        raise NotImplementedError("Remote storage does not support initialization.")

    def save(
        self,
        incoming_stream,
        size_limit=None,
        size=None,
        chunk_size=None,
        progress_callback=None,
    ):
        """Save file in the file system."""
        raise NotImplementedError("Remote storage does not support saving.")

    def update(
        self,
        incoming_stream,
        seek=0,
        size=None,
        chunk_size=None,
        progress_callback=None,
    ):
        """Update a file in the file system."""
        raise NotImplementedError("Remote storage does not support updating.")


def remote_storage_factory(
    fileinstance=None,
    default_location=None,
    default_storage_class=None,
    filestorage_class=RemoteFileStorage,
    fileurl=None,
    size=None,
    modified=None,
    clean_dir=True,
):
    """Get factory function for creating a PyFS file storage instance."""
    # Either the FileInstance needs to be specified or all filestorage
    # class parameters need to be specified
    assert fileinstance or (fileurl and size)

    if fileinstance:
        fileurl = fileinstance.uri

    return filestorage_class(fileurl, size=size, modified=modified)
