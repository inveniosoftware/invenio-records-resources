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

    Staged upload (prepare, write, and finalize replace FileContentComponent):

    +----------------------+     +----------------------+     +----------------------+
    | Components before,   |     | Write the bytes      |     | Finalize, then       |
    | then prepare         | --> | to storage           | --> | components after     |
    +----------------------+     +----------------------+     +----------------------+
    |----- short UoW ------|     |-- no DB connection --|     |----- short UoW ------|
"""

from dataclasses import dataclass
from typing import Optional, Type, Union
from uuid import UUID

from flask import current_app
from flask_babel import gettext as _
from invenio_db import db
from invenio_db.uow import ModelCommitOp, UnitOfWork
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.limiters import FileSizeLimit
from invenio_files_rest.models import Bucket, FileInstance, ObjectVersion
from invenio_files_rest.storage import FileStorage
from sqlalchemy.exc import DBAPIError, DisconnectionError, OperationalError
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import ClientDisconnected

from ...records.models import FileRecordModelMixin
from ..errors import FailedFileUploadException, TransferException
from ..uow import Operation, RecordCommitOp
from .components import FileContentComponent
from .components.base import FileServiceComponent
from .tasks import cleanup_failed_upload, discard_failed_upload
from .transfer import FETCH_TRANSFER_TYPE, LOCAL_TRANSFER_TYPE
from .transfer.providers.fetch import FetchTransfer
from .transfer.providers.local import LocalTransfer

STAGED_UPLOAD_MARKER = "_staged_upload"


class _CleanupUploadOp(Operation):
    """Clean staged storage after the deletion transaction commits."""

    def __init__(self, file_instance_id, uri):
        self.file_instance_id = str(file_instance_id)
        self.uri = uri

    def on_post_commit(self, uow):
        """Clean synchronously, scheduling retries for transient failures."""
        try:
            discard_failed_upload(self.file_instance_id, self.uri)
        except Exception:
            current_app.logger.exception("Failed to clean staged upload.")
            try:
                cleanup_failed_upload.delay(self.file_instance_id, self.uri)
            except Exception:
                current_app.logger.exception(
                    "Failed to schedule staged upload cleanup."
                )


@dataclass(frozen=True)
class _PreparedUpload:
    """Everything about an upload that outlives the transaction that set it up.

    The transaction closes before the bytes stream, so this holds ids rather
    than ORM objects, and every check re-reads the rows it names.
    """

    file_key: str
    record_id: UUID
    file_record_id: UUID
    file_record_model: Type[FileRecordModelMixin]
    object_version_id: UUID
    file_instance_id: UUID
    bucket_id: UUID
    uri: str
    storage: FileStorage
    size_limit: Optional[Union[int, FileSizeLimit]]

    def matches_file_record(self, file_record):
        """Say whether the record still points at the rows we prepared."""
        if file_record is None:
            return False
        obj = file_record.object_version
        return (
            obj is not None
            and file_record.object_version_id == self.object_version_id
            and obj.file_id == self.file_instance_id
        )

    def matches_file_instance(self, file_instance):
        """Say whether the row still holds the path we prepared."""
        return (
            file_instance is not None
            and not file_instance.readable
            and file_instance.uri == self.uri
        )

    def discard(self):
        """Remove what this upload set up, and nothing else.

        The row goes back to unused when the record still points at it, and is
        deleted when nothing does any more.
        """
        discard_failed_upload(self.file_instance_id, self.uri)


class UploadConflict(TransferException):
    """Another file operation got in the way of this upload."""


class UploadSuperseded(UploadConflict):
    """The rows this upload prepared are no longer the current ones."""


class FileUpload:
    """Upload files without holding a database connection."""

    def __init__(self, service):
        """Initialize the upload."""
        self.service = service

    def init(self, transfer, record, file_metadata, uow):
        """Initialize a file, preallocating rows for supported staged uploads."""
        if not self._supports_staged_upload(transfer):
            return transfer.init_file(record, file_metadata)

        file_instance = FileInstance.create()
        uow.register(ModelCommitOp(file_instance))
        obj = ObjectVersion.create(
            record.bucket,
            file_metadata["key"],
            _file_id=file_instance,
        )
        file_record = transfer.init_file(record, file_metadata, obj=obj)
        file_record[STAGED_UPLOAD_MARKER] = True
        file_record.commit()
        return file_record

    def set_content(
        self,
        identity,
        id_,
        record,
        file_key,
        stream,
        content_length,
        uow=None,
        expected_file_record_id=None,
    ):
        """Set file content using the upload path chosen during initialization."""
        if uow is not None:
            return self._set_classic_content(
                identity,
                id_,
                file_key,
                record,
                stream,
                content_length,
                uow=uow,
                expected_file_record_id=expected_file_record_id,
            )

        if self.uses_staged_upload(record.files.get(file_key)):
            return self._set_staged_content(
                identity,
                id_,
                record,
                file_key,
                stream,
                content_length,
                expected_file_record_id=expected_file_record_id,
            )

        return self._set_classic_content(
            identity,
            id_,
            file_key,
            record,
            stream,
            content_length,
            expected_file_record_id=expected_file_record_id,
        )

    def _set_staged_content(
        self,
        identity,
        id_,
        record,
        file_key,
        stream,
        content_length,
        *,
        expected_file_record_id=None,
    ):
        """Upload content without retaining a database connection."""
        return self._upload(
            record,
            file_key,
            stream,
            content_length,
            expected_file_record_id=expected_file_record_id,
        )

    def _set_classic_content(
        self,
        identity,
        id_,
        file_key,
        record,
        stream,
        content_length,
        uow=None,
        expected_file_record_id=None,
    ):
        """Upload content in one caller-managed or internal UoW."""
        if uow is not None:
            return self._set_content_in_uow(
                identity,
                id_,
                file_key,
                record,
                stream,
                content_length,
                uow=uow,
                expected_file_record_id=expected_file_record_id,
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
                expected_file_record_id=expected_file_record_id,
            )
            managed_uow.commit()
            return result

    def delete_file(self, identity, id_, record, file_key, uow=None):
        """Delete a file and any pending upload."""
        if self.uses_staged_upload(record.files[file_key]):
            if uow is not None:
                return self._delete_pending_upload_in_uow(
                    identity, id_, record, file_key, uow
                )
            return self._delete_pending_upload(identity, id_, record, file_key)

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

        with UnitOfWork(db.session) as managed_uow:
            deleted = self._delete_all_files_in_uow(identity, id_, record, managed_uow)
            managed_uow.commit()
            return deleted

    def uses_staged_upload(self, file_record):
        """Say whether this file is uploaded without holding a connection."""
        if file_record is None or file_record.transfer.transfer_type not in (
            LOCAL_TRANSFER_TYPE,
            FETCH_TRANSFER_TYPE,
        ):
            return False
        if not file_record.get(STAGED_UPLOAD_MARKER, False):
            return False
        obj = file_record.object_version
        return obj is not None and obj.file is not None and not obj.file.readable

    def _supports_staged_upload(self, transfer):
        """Say whether staged mode preserves the configured extension contracts."""
        if not current_app.config.get("RECORDS_RESOURCES_USE_STAGED_TRANSFER"):
            return False
        return self._supports_staged_contract(type(transfer))

    def _supports_staged_contract(self, transfer_cls):
        """Say whether transfer and component hooks match the built-in pipeline."""
        if transfer_cls not in (LocalTransfer, FetchTransfer):
            return False

        components = self.service.config.components
        try:
            components.index(FileContentComponent)
        except ValueError:
            return False

        for component_cls in components:
            set_content = getattr(component_cls, "set_file_content", None)
            if (
                component_cls is not FileContentComponent
                and set_content is not FileServiceComponent.set_file_content
            ):
                return False
        return True

    def _set_content_in_uow(
        self,
        identity,
        id_,
        file_key,
        record,
        stream,
        content_length,
        *,
        uow,
        expected_file_record_id=None,
    ):
        """Set file content in a transaction/UoW."""
        try:
            if expected_file_record_id is not None:
                current_file = (
                    uow.session.query(record.files[file_key].model.__class__)
                    .filter_by(id=expected_file_record_id, is_deleted=False)
                    .with_for_update()
                    .one_or_none()
                )
                if current_file is None:
                    raise UploadSuperseded(
                        f'File "{file_key}" was replaced before upload started.'
                    )
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
        self,
        identity,
        id_,
        file_key,
        record,
        uow,
        *,
        softdelete_obj=True,
        remove_rf=True,
    ):
        """Delete a file in a transaction/UoW."""
        deleted_file = record.files.delete(
            file_key, remove_rf=remove_rf, softdelete_obj=softdelete_obj
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
        results = []
        for file_key in file_keys:
            file_record = record.files[file_key]
            if self.uses_staged_upload(file_record):
                pending = self._lock_pending_upload(record, file_record, uow)
                if pending is not None:
                    file_instance_id, uri = pending
                    results.append(
                        record.files.delete(
                            file_key, softdelete_obj=False, remove_rf=True
                        )
                    )
                    uow.register(_CleanupUploadOp(file_instance_id, uri))
                else:
                    results.append(record.files.delete(file_key))
            else:
                results.append(record.files.delete(file_key))
        self.service.run_components(
            "delete_all_files", identity, id_, record, results, uow=uow
        )
        uow.register(RecordCommitOp(record))
        return results

    def _upload(
        self,
        record,
        file_key,
        stream,
        content_length,
        *,
        expected_file_record_id=None,
    ):
        """Upload content and return the file and any transfer error."""
        prepared = self._prepare(
            record,
            file_key,
            content_length,
            expected_file_record_id=expected_file_record_id,
        )
        try:
            written_uri, size, checksum = prepared.storage.save(
                stream,
                size=content_length,
                size_limit=prepared.size_limit,
            )
            if written_uri != prepared.uri:
                raise TransferException(
                    f'File "{file_key}" was written somewhere other than the '
                    "path prepared for it."
                )
        except FileSizeError as error:
            self._abort(record, prepared, error)
            raise
        except (ClientDisconnected, OSError):
            error = TransferException(f'Could not upload file "{file_key}".')
            return self._abort(record, prepared, error), error
        except Exception as error:
            # Storage backends raise their own errors (botocore, fsspec, ...).
            self._abort(record, prepared, error)
            raise

        try:
            self._finalize(prepared, size, checksum)
        except FileSizeError as error:
            self._abort(record, prepared, error)
            raise
        except UploadSuperseded:
            self._discard(prepared)
            raise
        except TransferException as error:
            return self._abort(record, prepared, error), error

        file_record = self.service.record_cls.pid.resolve(
            record.pid.pid_value, registered_only=False
        ).files[file_key]
        return file_record, None

    def _delete_pending_upload(self, identity, id_, record, file_key):
        """Delete a pending upload and its stored content."""
        with UnitOfWork(db.session) as uow:
            deleted_file = self._delete_pending_upload_in_uow(
                identity, id_, record, file_key, uow
            )
            uow.commit()
        return deleted_file

    def _delete_pending_upload_in_uow(self, identity, id_, record, file_key, uow):
        """Delete a pending upload as part of a caller-managed transaction."""
        file_record = record.files[file_key]
        pending = self._lock_pending_upload(record, file_record, uow)
        if pending is None:
            return self._delete_file_in_uow(identity, id_, file_key, record, uow)
        file_instance_id, uri = pending
        deleted_file = self._delete_file_in_uow(
            identity,
            id_,
            file_key,
            record,
            uow,
            softdelete_obj=False,
            remove_rf=True,
        )
        uow.register(_CleanupUploadOp(file_instance_id, uri))
        return deleted_file

    def _lock_pending_upload(self, record, file_record, uow):
        """Lock a pending upload and return its current cleanup coordinates."""
        uow.session.query(self.service.record_cls.model_cls).filter_by(
            id=record.id
        ).populate_existing().with_for_update().one()
        locked_file_record = (
            uow.session.query(file_record.model.__class__)
            .filter_by(id=file_record.id, is_deleted=False)
            .populate_existing()
            .with_for_update()
            .one()
        )
        object_version = (
            uow.session.query(ObjectVersion)
            .filter_by(version_id=locked_file_record.object_version_id)
            .populate_existing()
            .with_for_update()
            .one()
        )
        file_instance = (
            uow.session.query(FileInstance)
            .filter_by(id=object_version.file_id)
            .populate_existing()
            .with_for_update()
            .one()
        )
        if file_instance.readable:
            return None
        return file_instance.id, file_instance.uri

    def _prepare(
        self, record, file_key, content_length, *, expected_file_record_id=None
    ):
        """Take the file for this upload and initialize its storage path.

        Setting the uri while the file stays unreadable is what takes it: a
        second upload of the same key stops at the check below.
        """
        file_record = record.files[file_key]
        obj = file_record.object_version
        file_instance = obj.file
        storage = None
        storage_uri = None
        file_instance_id = file_instance.id
        prepared = None

        try:
            with UnitOfWork(db.session) as uow:
                # Lock the record, the file record, the object version and
                # the file instance so none of them can be deleted or pointed
                # somewhere else before this upload commits.
                uow.session.query(self.service.record_cls.model_cls).filter_by(
                    id=record.id
                ).populate_existing().with_for_update().one()
                locked_file_model = (
                    uow.session.query(file_record.model.__class__)
                    .filter_by(id=file_record.id, is_deleted=False)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )
                locked_object_version = (
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
                    expected_file_record_id is not None
                    and locked_file_model.id != expected_file_record_id
                ):
                    raise UploadSuperseded(
                        f'File "{file_key}" was replaced before upload started.'
                    )
                if (
                    locked_file_model.object_version_id
                    != locked_object_version.version_id
                    or locked_object_version.file_id != locked_file.id
                    or locked_file.readable
                    or locked_file.uri is not None
                ):
                    raise UploadConflict(
                        f'File "{file_key}" is already being uploaded.'
                    )

                bucket = record.bucket
                size_limit = bucket.size_limit
                if content_length and size_limit and content_length > size_limit:
                    raise FileSizeError(
                        description=self._size_limit_message(size_limit)
                    )

                storage = locked_file.storage(
                    default_location=bucket.location.uri,
                    default_storage_class=bucket.default_storage_class,
                )
                storage_uri, _, _ = storage.initialize()
                locked_file.set_uri(
                    storage_uri,
                    0,
                    None,
                    readable=False,
                    writable=True,
                )
                prepared = _PreparedUpload(
                    file_key=file_key,
                    record_id=record.id,
                    file_record_id=file_record.id,
                    file_record_model=file_record.model.__class__,
                    object_version_id=obj.version_id,
                    file_instance_id=file_instance_id,
                    bucket_id=bucket.id,
                    uri=storage_uri,
                    storage=storage,
                    size_limit=size_limit,
                )
                uow.commit()

            return prepared
        except Exception as error:
            db.session.rollback()
            if storage is not None and storage_uri is not None:
                # The commit may have gone through before the error, so check
                # whether the file was prepared after all. Read it in its
                # own transaction: the caller streams next and must not hold a
                # connection open.
                prepare_committed = False
                with UnitOfWork(db.session) as uow:
                    current_file_instance = uow.session.get(
                        FileInstance, file_instance_id
                    )
                    prepare_committed = (
                        prepared is not None
                        and current_file_instance is not None
                        and current_file_instance.uri == storage_uri
                    )
                    uow.commit()
                if prepare_committed:
                    return prepared
                storage.delete()
            if isinstance(error, NoResultFound):
                raise UploadConflict(
                    f'File "{file_key}" was deleted while it was being uploaded.'
                ) from error
            raise

    def _finalize(self, prepared, size, checksum, retry=True):
        """Make the file readable and add its size to the bucket."""
        try:
            with UnitOfWork(db.session) as uow:
                # Lock the same rows again, so nothing can delete or re-point
                # them while this upload is being finished.
                bucket = (
                    uow.session.query(Bucket)
                    .filter_by(id=prepared.bucket_id, deleted=False)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )
                uow.session.query(self.service.record_cls.model_cls).filter_by(
                    id=prepared.record_id, is_deleted=False
                ).populate_existing().with_for_update().one()
                file_record_row = (
                    uow.session.query(prepared.file_record_model)
                    .filter_by(id=prepared.file_record_id, is_deleted=False)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )
                object_version = (
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

                # Someone deleted the file and re-initialized the same key, so
                # the record now points at rows a later upload created.
                if (
                    file_record_row.object_version_id != object_version.version_id
                    or object_version.file_id != file_instance.id
                ):
                    raise UploadSuperseded(
                        f'File "{prepared.file_key}" was replaced while it was '
                        "being uploaded."
                    )
                if file_instance.readable:
                    # This is a retry and the first attempt did commit after
                    # all: our bytes are already there, so there is nothing
                    # left to do.
                    if (
                        file_instance.uri == prepared.uri
                        and file_instance.size == size
                        and file_instance.checksum == checksum
                    ):
                        uow.commit()
                        return
                    # The row holds someone else's content.
                    raise UploadSuperseded(
                        f'File "{prepared.file_key}" was uploaded by someone else.'
                    )
                # Another upload took the row again and wrote its own path.
                if file_instance.uri != prepared.uri:
                    raise UploadSuperseded(
                        f'File "{prepared.file_key}" was replaced while it was '
                        "being uploaded."
                    )

                size_limit = bucket.size_limit
                if size_limit and size > size_limit:
                    raise FileSizeError(
                        description=self._size_limit_message(size_limit)
                    )

                file_instance.set_uri(
                    prepared.uri, size, checksum, readable=True, writable=False
                )
                bucket.size += size
                uow.commit()
        except NoResultFound as error:
            # One of the rows we locked was deleted while we streamed.
            db.session.rollback()
            raise UploadSuperseded(
                f'File "{prepared.file_key}" was deleted while it was being uploaded.'
            ) from error
        except (FileSizeError, TransferException):
            raise
        except Exception as error:
            db.session.rollback()
            try:
                finalized = self._is_finalized(prepared, size, checksum)
            except Exception:
                self._schedule_cleanup(prepared)
                raise error
            if finalized:
                # The commit went through and the error came afterwards, so
                # the file is finished and there is nothing left to do.
                return
            if retry and self._is_connection_lost(error):
                # A connection that went stale during the long write is the
                # only failure worth repeating, on a fresh checkout. Anything
                # else would run the components a second time.
                return self._finalize(
                    prepared,
                    size,
                    checksum,
                    retry=False,
                )
            # We cannot finish, so hand the reservation to a task that undoes
            # it, retrying with backoff.
            self._schedule_cleanup(prepared)
            raise

    @staticmethod
    def _is_finalized(prepared, size, checksum):
        """Say whether the failed commit went through anyway.

        Read in its own transaction, so the failed one is not left open.
        """
        with UnitOfWork(db.session) as uow:
            file_instance = uow.session.get(FileInstance, prepared.file_instance_id)
            finished = (
                file_instance is not None
                and file_instance.readable
                and file_instance.uri == prepared.uri
                and file_instance.size == size
                and file_instance.checksum == checksum
            )
            uow.commit()
        return finished

    def _abort(self, record, prepared, exception):
        """Record a fetch failure or remove a failed local upload."""
        try:
            with UnitOfWork(db.session) as uow:
                uow.session.query(self.service.record_cls.model_cls).filter_by(
                    id=prepared.record_id
                ).populate_existing().with_for_update().one()
                file_record_row = (
                    uow.session.query(prepared.file_record_model)
                    .filter_by(id=prepared.file_record_id, is_deleted=False)
                    .populate_existing()
                    .with_for_update()
                    .one()
                )
                object_version = (
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
                    file_record_row.object_version_id != object_version.version_id
                    or object_version.file_id != file_instance.id
                    or not prepared.matches_file_instance(file_instance)
                ):
                    raise UploadSuperseded(
                        f'File "{prepared.file_key}" was replaced while its upload '
                        "was being aborted."
                    )

                record = self.service.record_cls.pid.resolve(
                    record.pid.pid_value, registered_only=False
                )
                file_record = record.files.get(prepared.file_key)
                if not prepared.matches_file_record(file_record):
                    raise UploadSuperseded(
                        f'File "{prepared.file_key}" was replaced while its upload '
                        "was being aborted."
                    )

                if file_record.transfer.transfer_type == FETCH_TRANSFER_TYPE:
                    file_record.transfer["error"] = str(exception)
                    file_record.object_version = None
                    file_record.object_version_id = None
                    object_version.remove()
                    uow.register(RecordCommitOp(file_record))
                    failed = file_record
                else:
                    failed = record.files.delete(
                        prepared.file_key, softdelete_obj=False, remove_rf=True
                    )
                    uow.register(RecordCommitOp(record))
                uow.commit()
                return failed
        except NoResultFound as error:
            db.session.rollback()
            raise UploadSuperseded(
                f'File "{prepared.file_key}" was deleted while its upload was '
                "being aborted."
            ) from error
        finally:
            self._discard(prepared)

    @staticmethod
    def _discard(prepared):
        """Discard an upload now, scheduling a retry if cleanup fails."""
        try:
            prepared.discard()
        except Exception:
            current_app.logger.exception("Failed to discard staged upload.")
            try:
                cleanup_failed_upload.delay(
                    str(prepared.file_instance_id), prepared.uri
                )
            except Exception:
                current_app.logger.exception(
                    "Failed to schedule staged upload cleanup."
                )

    @staticmethod
    def _schedule_cleanup(prepared):
        """Best-effort publication of retryable cleanup."""
        try:
            cleanup_failed_upload.delay(str(prepared.file_instance_id), prepared.uri)
        except Exception:
            current_app.logger.exception("Failed to schedule staged upload cleanup.")

    @staticmethod
    def _is_connection_lost(error):
        """Say whether the database dropped the connection."""
        if isinstance(error, DisconnectionError):
            return True
        return isinstance(error, (OperationalError, DBAPIError)) and getattr(
            error, "connection_invalidated", False
        )

    @staticmethod
    def _size_limit_message(size_limit):
        """Return the file-size error message."""
        return (
            _("File size limit exceeded.")
            if isinstance(size_limit, int)
            else size_limit.reason
        )
