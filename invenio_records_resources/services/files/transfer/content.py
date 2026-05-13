# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Staged transfer content handle and shared transfer-class behaviour."""

from flask_babel import gettext as _
from invenio_db.uow import ModelCommitOp
from invenio_files_rest import current_files_rest
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import Bucket, FileInstance, ObjectVersion
from sqlalchemy import update
from werkzeug.exceptions import ClientDisconnected

from ...errors import TransferException
from ...uow import RecordCommitOp
from .base import TransferStatus


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


class StagedTransferMixin:
    """Shared behaviour for staged transfer classes.

    Subclasses must also inherit a concrete ``Transfer`` (e.g. ``LocalTransfer``
    or ``FetchTransfer``) and set ``transfer_type`` and
    ``supports_staged_content = True``.
    """

    supports_staged_content = True

    def init_file(self, record, file_metadata, **kwargs):
        """Pre-allocate FI + OV, then chain to the parent transfer's init."""
        file_instance = FileInstance.create()
        self.uow.register(ModelCommitOp(file_instance))

        version = ObjectVersion.create(
            record.bucket, file_metadata["key"], _file_id=file_instance
        )

        file_record = super().init_file(record, file_metadata, obj=version, **kwargs)
        self.uow.register(RecordCommitOp(file_record))
        return file_record

    def begin_content(self, content_length):
        """Validate state and return a ready-to-write StagedContentHandle."""
        ov = self.file_record.object_version
        if ov is None or ov.file is None:
            raise TransferException(
                _(
                    f'Staged file "{self.file_record.key}" is missing'
                    " pre-allocated state."
                )
            )
        if ov.file.readable:
            raise TransferException(
                _(f'File with key "{self.file_record.key}" is already committed.')
            )

        bucket = self.record.bucket
        size_limit = bucket.size_limit
        if content_length and size_limit and content_length > size_limit:
            desc = (
                _("File size limit exceeded.")
                if isinstance(size_limit, int)
                else size_limit.reason
            )
            raise FileSizeError(description=desc)

        fi = ov.file
        storage = current_files_rest.storage_factory(
            fileinstance=fi,
            default_location=bucket.location.uri,
            default_storage_class=bucket.default_storage_class,
        )
        # Plain values only — no ORM references survive the begin/finalize
        # boundary, so the surrounding txn can commit before bytes flow.
        return StagedContentHandle(
            file_instance_id=fi.id,
            bucket_id=bucket.id,
            storage=storage,
            size_limit=size_limit,
            file_key=self.file_record.key,
        )

    def _ensure_staged_finalized(self):
        """Raise if finalize hasn't marked the FileInstance readable."""
        ov = self.file_record.object_version
        fi = ov.file if ov is not None else None
        if fi is None or not fi.readable:
            raise TransferException(
                _(
                    f'Staged upload for file "{self.file_record.key}"'
                    " has not finalized."
                )
            )

    @property
    def status(self):
        """Pending until the FileInstance is readable."""
        if self.file_record is None:
            return TransferStatus.PENDING
        ov = self.file_record.object_version
        if ov is None or ov.file is None or not ov.file.readable:
            return TransferStatus.PENDING
        return TransferStatus.COMPLETED
