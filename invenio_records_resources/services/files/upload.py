# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""File uploads that release the database connection while streaming.

Upload paths::

    Regular upload:

    +----------------------+     +----------------------+     +----------------------+
    | Components before    |     | FileContentComponent |     | Components after     |
    | FileContentComponent | --> | saves to storage     | --> | FileContentComponent |
    +----------------------+     +----------------------+     +----------------------+
    |----------------------------------- one UoW ------------------------------------|

    Staged upload (claim, save, and finalize replace FileContentComponent):

    +----------------------+     +----------------------+     +----------------------+
    | Components before,   |     | Stream bytes         |     | Finalize file, then  |
    | then claim the file  | --> | to storage           | --> | components after     |
    +----------------------+     +----------------------+     +----------------------+
    |----- short UoW ------|     |-- no DB connection --|     |----- short UoW ------|
"""

from dataclasses import dataclass
from typing import Optional, Type, Union
from uuid import UUID

from flask import current_app
from flask_babel import gettext as _
from invenio_db import db
from invenio_db.uow import UnitOfWork
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.limiters import FileSizeLimit
from invenio_files_rest.models import Bucket, FileInstance, ObjectVersion
from invenio_files_rest.storage import FileStorage
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import ClientDisconnected

from ...records.models import FileRecordModelMixin
from ..errors import FailedFileUploadException, TransferException
from ..uow import RecordCommitOp
from .components import FileContentComponent
from .transfer import FETCH_TRANSFER_TYPE, LOCAL_TRANSFER_TYPE


@dataclass(frozen=True)
class _PreparedUpload:
    """Values needed after the upload transaction closes."""

    record_id: UUID
    file_record_id: UUID
    file_record_model: Type[FileRecordModelMixin]
    object_version_id: UUID
    file_instance_id: UUID
    bucket_id: UUID
    file_key: str
    storage: FileStorage
    size_limit: Optional[Union[int, FileSizeLimit]]


class UploadConflict(TransferException):
    """The upload has already been claimed or deleted."""


class FileUpload:
    """Upload files without holding a database connection."""

    def __init__(self, service):
        """Initialize the upload."""
        self.service = service

    def set_content(
        self, identity, id_, record, file_key, stream, content_length, uow=None
    ):
        """Set file content using the upload path chosen during initialization."""
        if uow is not None:
            return self._set_content_in_uow(
                identity,
                id_,
                file_key,
                record,
                stream,
                content_length,
                uow=uow,
            )

        if self.handles(record.files.get(file_key)):
            component_args = (identity, id_, file_key, stream, content_length)
            before_components, after_components = self._split_content_components()
            return self._upload(
                record,
                file_key,
                stream,
                content_length,
                before_components=before_components,
                after_components=after_components,
                component_args=component_args,
            )

        with UnitOfWork(db.session) as managed_uow:
            result = self._set_content_in_uow(
                identity,
                id_,
                file_key,
                record,
                stream,
                content_length,
                uow=managed_uow,
            )
            managed_uow.commit()
            return result

    def delete_file(self, identity, id_, record, file_key, uow=None):
        """Delete a file and any pending upload."""
        if uow is None and self.handles(record.files[file_key]):
            return self._delete_pending(identity, id_, record, file_key)

        if uow is not None:
            return self._delete_file_in_uow(identity, id_, file_key, record, uow)

        with UnitOfWork(db.session) as managed_uow:
            deleted_file = self._delete_file_in_uow(
                identity, id_, file_key, record, managed_uow
            )
            managed_uow.commit()
            return deleted_file

    def delete_all_files(self, identity, id_, record, uow=None):
        """Delete all files and pending uploads."""
        if uow is not None:
            return self._delete_all_files_in_uow(identity, id_, record, uow)

        file_keys = list(record.files)
        deleted = {}
        for file_key in file_keys:
            if self.handles(record.files[file_key]):
                deleted[file_key] = self._delete_pending(
                    identity, id_, record, file_key
                )
                record = self.service.record_cls.pid.resolve(id_, registered_only=False)

        with UnitOfWork(db.session) as managed_uow:
            remaining = self._delete_all_files_in_uow(
                identity, id_, record, managed_uow
            )
            managed_uow.commit()
        deleted.update({file.key: file for file in remaining})
        return [deleted[file_key] for file_key in file_keys]

    @staticmethod
    def handles(file_record):
        """Check whether a file uses this upload path."""
        if file_record is None or file_record.transfer.transfer_type not in (
            LOCAL_TRANSFER_TYPE,
            FETCH_TRANSFER_TYPE,
        ):
            return False
        obj = file_record.object_version
        return obj is not None and obj.file is not None and not obj.file.readable

    def _set_content_in_uow(
        self, identity, id_, file_key, record, stream, content_length, *, uow
    ):
        """Set file content in a transaction/UoW."""
        try:
            self.service.run_components(
                "set_file_content",
                identity,
                id_,
                file_key,
                stream,
                content_length,
                record,
                uow=uow,
            )
            return record.files[file_key], None
        except FailedFileUploadException as error:
            current_app.logger.exception("File upload transfer failed.")
            # Commit the cleanup operation registered by FileContentComponent.
            return error.file, error

    def _delete_file_in_uow(
        self, identity, id_, file_key, record, uow, *, softdelete_obj=True
    ):
        """Delete a file in a transaction/UoW."""
        deleted_file = record.files.delete(
            file_key, remove_rf=True, softdelete_obj=softdelete_obj
        )
        self.service.run_components(
            "delete_file", identity, id_, file_key, record, deleted_file, uow=uow
        )
        # Deleting a file can change default_preview.
        uow.register(RecordCommitOp(record))
        return deleted_file

    def _delete_all_files_in_uow(self, identity, id_, record, uow):
        """Delete all files in a transaction/UoW."""
        file_keys = list(record.files)
        results = [record.files.delete(file_key) for file_key in file_keys]
        self.service.run_components(
            "delete_all_files", identity, id_, record, results, uow=uow
        )
        uow.register(RecordCommitOp(record))
        return results

    def _split_content_components(self):
        """Preserve component order around the staged storage write.

        Staged uploads replace ``FileContentComponent``. Components before it
        join the claim UoW, while components after it join the finalize UoW.
        This keeps only the storage write outside a database transaction.
        """
        before = []
        after = []
        content_seen = False
        for component_cls in self.service.config.components:
            if issubclass(component_cls, FileContentComponent):
                content_seen = True
            elif content_seen:
                after.append(component_cls)
            else:
                before.append(component_cls)
        return before, after

    def _run_set_content_components(self, component_classes, args, record, uow):
        """Run set-content components in the given UoW."""
        for component_cls in component_classes:
            component = component_cls(self.service)
            component.uow = uow
            try:
                component.set_file_content(*args, record)
            finally:
                component.uow = None

    def _upload(
        self,
        record,
        file_key,
        stream,
        content_length,
        *,
        before_components=(),
        after_components=(),
        component_args=(),
    ):
        """Upload content and return the file and any transfer error."""
        prepared = self._prepare(
            record,
            file_key,
            content_length,
            components=before_components,
            component_args=component_args,
        )
        try:
            uri, size, checksum = prepared.storage.save(
                stream,
                size=content_length,
                size_limit=prepared.size_limit,
            )
        except FileSizeError as error:
            self._abort(record, file_key, error, cleanup_storage=False)
            raise
        except (ClientDisconnected, OSError):
            error = TransferException(f'Transfer of File with key "{file_key}" failed.')
            return (
                self._abort(record, file_key, error, cleanup_storage=False),
                error,
            )

        try:
            self._finalize(
                prepared,
                uri,
                size,
                checksum,
                components=after_components,
                component_args=component_args,
            )
        except FileSizeError as error:
            self._abort(record, file_key, error, cleanup_storage=True)
            raise
        except UploadConflict:
            prepared.storage.delete()
            raise
        except TransferException as error:
            return self._abort(record, file_key, error, cleanup_storage=True), error

        file_record = self.service.record_cls.pid.resolve(
            record.pid.pid_value, registered_only=False
        ).files[file_key]
        return file_record, None

    def _delete_pending(self, identity, id_, record, file_key):
        """Delete a pending upload and its stored content."""
        file_instance = record.files[file_key].object_version.file
        file_instance_id = file_instance.id
        storage = file_instance.storage() if file_instance.uri else None

        with UnitOfWork(db.session) as uow:
            deleted_file = self._delete_file_in_uow(
                identity,
                id_,
                file_key,
                record,
                uow,
                softdelete_obj=False,
            )
            uow.commit()

        if storage is not None:
            storage.delete()

        with UnitOfWork(db.session) as uow:
            durable_file = uow.session.get(FileInstance, file_instance_id)
            if durable_file is not None:
                durable_file.delete()
            uow.commit()

        return deleted_file

    def _prepare(
        self, record, file_key, content_length, *, components=(), component_args=()
    ):
        """Claim the file and initialize its storage path."""
        file_record = record.files[file_key]
        obj = file_record.object_version
        file_instance = obj.file
        storage = None
        initialized_uri = None
        file_instance_id = file_instance.id
        prepared_values = None

        try:
            with UnitOfWork(db.session) as uow:
                self._run_set_content_components(
                    components, component_args, record, uow
                )
                # Refresh and lock the ownership chain before claiming the upload.
                uow.session.query(self.service.record_cls.model_cls).filter_by(
                    id=record.id
                ).populate_existing().with_for_update().one()
                model = (
                    uow.session.query(file_record.model.__class__)
                    .filter_by(id=file_record.id, is_deleted=False)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )
                locked_obj = (
                    uow.session.query(ObjectVersion)
                    .filter_by(version_id=obj.version_id)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )
                locked_file = (
                    uow.session.query(FileInstance)
                    .filter_by(id=file_instance_id)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )
                if (
                    model.object_version_id != locked_obj.version_id
                    or locked_obj.file_id != locked_file.id
                    or locked_file.readable
                    or locked_file.uri is not None
                ):
                    raise UploadConflict(
                        f'Upload for file "{file_key}" has already been claimed.'
                    )

                bucket = record.bucket
                size_limit = bucket.size_limit
                if content_length and size_limit and content_length > size_limit:
                    raise FileSizeError(description=self._size_limit_error(size_limit))

                storage = locked_file.storage(
                    default_location=bucket.location.uri,
                    default_storage_class=bucket.default_storage_class,
                )
                initialized_uri, _, _ = storage.initialize()
                locked_file.set_uri(
                    initialized_uri,
                    0,
                    None,
                    readable=False,
                    writable=True,
                )
                prepared_values = {
                    "record_id": record.id,
                    "file_record_id": file_record.id,
                    "file_record_model": file_record.model.__class__,
                    "object_version_id": obj.version_id,
                    "file_instance_id": file_instance_id,
                    "bucket_id": bucket.id,
                    "file_key": file_key,
                    "storage": storage,
                    "size_limit": size_limit,
                }
                uow.commit()

            return _PreparedUpload(**prepared_values)
        except Exception as error:
            db.session.rollback()
            if storage is not None and initialized_uri is not None:
                durable_file = db.session.get(FileInstance, file_instance_id)
                if (
                    prepared_values is not None
                    and durable_file is not None
                    and durable_file.uri == initialized_uri
                ):
                    return _PreparedUpload(**prepared_values)
                storage.delete()
            if isinstance(error, NoResultFound):
                raise UploadConflict(
                    f'Upload for file "{file_key}" no longer owns the file.'
                ) from error
            raise

    def _finalize(
        self,
        prepared,
        uri,
        size,
        checksum,
        retry=True,
        *,
        components=(),
        component_args=(),
    ):
        """Mark the file readable and add its size to the bucket."""
        try:
            with UnitOfWork(db.session) as uow:
                # Refresh and lock the ownership chain before finalizing the upload.
                bucket = (
                    uow.session.query(Bucket)
                    .filter_by(id=prepared.bucket_id)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )
                uow.session.query(self.service.record_cls.model_cls).filter_by(
                    id=prepared.record_id
                ).populate_existing().with_for_update().one()
                file_model = (
                    uow.session.query(prepared.file_record_model)
                    .filter_by(id=prepared.file_record_id, is_deleted=False)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )
                obj = (
                    uow.session.query(ObjectVersion)
                    .filter_by(version_id=prepared.object_version_id)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )
                file_instance = (
                    uow.session.query(FileInstance)
                    .filter_by(id=prepared.file_instance_id)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )

                if (
                    file_model.object_version_id != obj.version_id
                    or obj.file_id != file_instance.id
                ):
                    raise TransferException(
                        f'Upload for file "{prepared.file_key}" no longer owns '
                        "the file."
                    )
                if file_instance.readable:
                    if (
                        file_instance.uri == uri
                        and file_instance.size == size
                        and file_instance.checksum == checksum
                    ):
                        uow.commit()
                        return
                    raise TransferException(
                        f'File with key "{prepared.file_key}" is already committed.'
                    )
                if file_instance.uri != uri:
                    raise TransferException(
                        f'Upload for file "{prepared.file_key}" lost its claim.'
                    )

                size_limit = bucket.size_limit
                if size_limit and size > size_limit:
                    raise FileSizeError(description=self._size_limit_error(size_limit))

                file_instance.set_uri(
                    uri, size, checksum, readable=True, writable=False
                )
                bucket.size += size
                if components:
                    record = self.service.record_cls.pid.resolve(
                        component_args[1], registered_only=False
                    )
                    self._run_set_content_components(
                        components, component_args, record, uow
                    )
                uow.commit()
        except NoResultFound as error:
            db.session.rollback()
            raise UploadConflict(
                f'Upload for file "{prepared.file_key}" no longer owns the file.'
            ) from error
        except (FileSizeError, TransferException):
            raise
        except Exception:
            db.session.rollback()
            durable = db.session.get(FileInstance, prepared.file_instance_id)
            if (
                durable is not None
                and durable.readable
                and durable.uri == uri
                and durable.size == size
                and durable.checksum == checksum
            ):
                return
            if retry and durable is not None and not durable.readable:
                return self._finalize(
                    prepared,
                    uri,
                    size,
                    checksum,
                    retry=False,
                    components=components,
                    component_args=component_args,
                )
            raise

    def _abort(self, record, file_key, exception, cleanup_storage):
        """Record a fetch failure or remove a failed local upload."""
        file_record = record.files[file_key]
        obj = file_record.object_version
        file_instance = obj.file
        file_instance_id = file_instance.id
        storage = file_instance.storage() if cleanup_storage else None

        if file_record.transfer.transfer_type == FETCH_TRANSFER_TYPE:
            with UnitOfWork(db.session) as uow:
                file_record.transfer["error"] = str(exception)
                file_record.object_version = None
                file_record.object_version_id = None
                obj.remove()
                uow.register(RecordCommitOp(file_record))
                uow.commit()
            failed = file_record
        else:
            with UnitOfWork(db.session) as uow:
                failed = record.files.delete(
                    file_key, softdelete_obj=False, remove_rf=True
                )
                uow.commit()

        if storage is not None:
            storage.delete()

        with UnitOfWork(db.session) as uow:
            durable_file = uow.session.get(FileInstance, file_instance_id)
            if durable_file is not None:
                durable_file.delete()
            uow.commit()

        return failed

    @staticmethod
    def _size_limit_error(size_limit):
        """Return the file-size error message."""
        return (
            _("File size limit exceeded.")
            if isinstance(size_limit, int)
            else size_limit.reason
        )
