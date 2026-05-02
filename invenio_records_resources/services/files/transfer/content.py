# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Staged content handle."""

from invenio_db.uow import ModelCommitOp
from invenio_files_rest.models import Bucket, FileInstance
from sqlalchemy import update
from werkzeug.exceptions import ClientDisconnected

from ...errors import TransferException


class StagedContentHandle:
    """Context-manager handle for a single staged-local upload."""

    def __init__(
        self,
        *,
        file_instance_id,
        bucket_id,
        storage,
        size_limit,
        file_key,
    ):
        """Construct the handle from pre-captured values."""
        self.file_instance_id = file_instance_id
        self.bucket_id = bucket_id
        self.storage = storage
        self.size_limit = size_limit
        self.file_key = file_key
        self.uri = None
        self.size = None
        self.checksum = None
        self._finalized = False

    def __enter__(self):
        """Enter the handle context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Best-effort storage cleanup if write succeeded but finalize did not."""
        if exc_type is not None and self.uri and not self._finalized:
            try:
                self.storage.delete()
            except Exception:
                pass
        return False

    def write(self, stream, content_length):
        """Stream bytes to storage and capture URI, size, checksum."""
        try:
            self.uri, self.size, self.checksum = self.storage.save(
                stream,
                size=content_length,
                size_limit=self.size_limit,
            )
        except (ClientDisconnected, OSError) as exc:
            raise TransferException(
                f'Transfer of File with key "{self.file_key}" failed.'
            ) from exc

    def finalize(self, *, uow):
        """Promote the FileInstance to readable and add its size to the bucket."""
        fi = uow.session.get(FileInstance, self.file_instance_id)
        fi.set_uri(self.uri, self.size, self.checksum, readable=True, writable=False)
        uow.register(ModelCommitOp(fi))
        uow.session.execute(
            update(Bucket)
            .where(Bucket.id == self.bucket_id)
            .values(size=Bucket.size + self.size)
        )
        self._finalized = True
