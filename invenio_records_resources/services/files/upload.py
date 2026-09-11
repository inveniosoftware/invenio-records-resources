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
from invenio_db.uow import UnitOfWork
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.limiters import FileSizeLimit
from invenio_files_rest.models import Bucket, FileInstance, ObjectVersion
from invenio_files_rest.storage import FileStorage
from sqlalchemy.exc import DBAPIError, DisconnectionError, OperationalError
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import ClientDisconnected

from ...records.models import FileRecordModelMixin
from ..errors import FailedFileUploadException, TransferException
from ..uow import RecordCommitOp
from .components import FileContentComponent
from .tasks import cleanup_failed_upload
from .transfer import FETCH_TRANSFER_TYPE, LOCAL_TRANSFER_TYPE


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
        try:
            self.storage.delete()
        except FileNotFoundError:
            # A concurrent delete already removed the file.
            pass

        with UnitOfWork(db.session) as uow:
            file_instance = (
                uow.session.query(FileInstance)
                .filter_by(id=self.file_instance_id)
                .populate_existing()
                .with_for_update()
                .one_or_none()
            )
            if self.matches_file_instance(file_instance):
                object_version_count = (
                    uow.session.query(ObjectVersion)
                    .filter_by(file_id=self.file_instance_id)
                    .count()
                )
                if object_version_count:
                    # An object version points at the row, and deleting it
                    # would break that foreign key. Reset it instead, so the
                    # file goes back to pending and can be uploaded again.
                    # An UPDATE, because the model's uri validator rejects None.
                    uow.session.query(FileInstance).filter_by(
                        id=self.file_instance_id
                    ).update(
                        {
                            "uri": None,
                            "size": 0,
                            "checksum": None,
                            "readable": False,
                            "writable": True,
                        },
                        synchronize_session=False,
                    )
                else:
                    file_instance.delete()
            uow.commit()


class UploadConflict(TransferException):
    """Another file operation got in the way of this upload."""


class UploadSuperseded(UploadConflict):
    """The rows this upload prepared are no longer the current ones."""


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

        if self.uses_staged_upload(record.files.get(file_key)):
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
        if uow is None and self.uses_staged_upload(record.files[file_key]):
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

        file_keys = list(record.files)
        deleted = {}
        for file_key in file_keys:
            if self.uses_staged_upload(record.files[file_key]):
                deleted[file_key] = self._delete_pending_upload(
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
    def uses_staged_upload(file_record):
        """Say whether this file is uploaded without holding a connection."""
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
        join the prepare transaction, those after it join the finalize one.
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
            self._finalize(
                prepared,
                size,
                checksum,
                components=after_components,
                component_args=component_args,
            )
        except FileSizeError as error:
            self._abort(record, prepared, error)
            raise
        except UploadSuperseded:
            prepared.discard()
            raise
        except TransferException as error:
            return self._abort(record, prepared, error), error

        file_record = self.service.record_cls.pid.resolve(
            record.pid.pid_value, registered_only=False
        ).files[file_key]
        return file_record, None

    def _delete_pending_upload(self, identity, id_, record, file_key):
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
            current_file_instance = uow.session.get(FileInstance, file_instance_id)
            if current_file_instance is not None:
                current_file_instance.delete()
            uow.commit()

        return deleted_file

    def _prepare(
        self, record, file_key, content_length, *, components=(), component_args=()
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
                self._run_set_content_components(
                    components, component_args, record, uow
                )
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

    def _finalize(
        self,
        prepared,
        size,
        checksum,
        retry=True,
        *,
        components=(),
        component_args=(),
    ):
        """Make the file readable and add its size to the bucket."""
        try:
            with UnitOfWork(db.session) as uow:
                # Lock the same rows again, so nothing can delete or re-point
                # them while this upload is being finished.
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
                if components:
                    record = self.service.record_cls.pid.resolve(
                        component_args[1], registered_only=False
                    )
                    self._run_set_content_components(
                        components, component_args, record, uow
                    )
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
            if self._is_finalized(prepared, size, checksum):
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
                    components=components,
                    component_args=component_args,
                )
            # We cannot finish, so hand the reservation to a task that undoes
            # it, retrying with backoff.
            cleanup_failed_upload.delay(str(prepared.file_instance_id), prepared.uri)
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
        record = self.service.record_cls.pid.resolve(
            record.pid.pid_value, registered_only=False
        )
        file_record = record.files.get(prepared.file_key)

        if not prepared.matches_file_record(file_record):
            # The key was deleted and re-initialized while we streamed, so the
            # file record belongs to a later upload. Only our own rows go.
            prepared.discard()
            return file_record

        if file_record.transfer.transfer_type == FETCH_TRANSFER_TYPE:
            with UnitOfWork(db.session) as uow:
                file_record.transfer["error"] = str(exception)
                obj = file_record.object_version
                file_record.object_version = None
                file_record.object_version_id = None
                obj.remove()
                uow.register(RecordCommitOp(file_record))
                uow.commit()
            failed = file_record
        else:
            with UnitOfWork(db.session) as uow:
                failed = record.files.delete(
                    prepared.file_key, softdelete_obj=False, remove_rf=True
                )
                uow.commit()

        prepared.discard()
        return failed

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
