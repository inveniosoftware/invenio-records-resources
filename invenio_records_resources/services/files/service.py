# SPDX-FileCopyrightText: 2020-2026 CERN.
# SPDX-FileCopyrightText: 2020-2021 Northwestern University.
# SPDX-FileCopyrightText: 2025 CESNET i.a.l.e.
# SPDX-License-Identifier: MIT

"""File Service API."""

from flask import current_app
from invenio_i18n import gettext as _
from marshmallow import ValidationError

from invenio_records_resources.proxies import current_transfer_registry
from invenio_records_resources.services.files.transfer import TransferStatus

from ..base import LinksTemplate, Service
from ..errors import (
    ArchiveDownloadTooLargeException,
    FailedFileUploadException,
    FileKeyNotFoundError,
    NoExtractorFoundError,
)
from ..records.schema import ServiceSchemaWrapper
from ..uow import RecordCommitOp, unit_of_work
from .schema import InitFileSchemaMixin


class FileService(Service):
    """A service for adding files support to records."""

    @property
    def record_cls(self):
        """Get the record class."""
        return self.config.record_cls

    @property
    def file_schema(self):
        """Returns the data schema instance.

        The schema can be used for dumping file's metadata or updating them.
        For the creation of a new file, use the `initial_file_schema` property
        as it will include the necessary fields for initiating the file upload.
        """
        return ServiceSchemaWrapper(self, schema=self.config.file_schema)

    @property
    def initial_file_schema(self):
        """Returns the data schema instance for initiating the file upload."""
        if not hasattr(self.config, "initial_file_schema"):
            self.config.initial_file_schema = type(
                self.config.file_schema.__name__ + "Initial",
                (
                    InitFileSchemaMixin,
                    self.config.file_schema,
                ),
                {},
            )
        return ServiceSchemaWrapper(self, schema=self.config.initial_file_schema)

    def file_result_item(self, *args, **kwargs):
        """Create a new instance of the resource unit."""
        return self.config.file_result_item_cls(*args, **kwargs)

    def file_result_list(self, *args, **kwargs):
        """Create a new instance of the resource list."""
        return self.config.file_result_list_cls(*args, **kwargs)

    def file_result_container_list(self, *args, **kwargs):
        """Create a new instance of the resource listing."""
        return self.config.file_result_container_list_cls(*args, **kwargs)

    def file_result_container_item(self, *args, **kwargs):
        """Create a new instance of the resource listing."""
        return self.config.file_result_container_item_cls(*args, **kwargs)

    def file_links_list_tpl(self, id_):
        """Return a link template for list results."""
        return LinksTemplate(
            # Until all modules have transitioned to using invenio_url_for,
            # we have to keep `id` in context for URL expansion
            self.config.file_links_list,
            context={"id": id_, "pid_value": id_},
        )

    def container_item_links_list_tpl(self, id_, key):
        """Return a link template for list results."""
        return LinksTemplate(
            # Until all modules have transitioned to using invenio_url_for,
            # we have to keep `id` in context for URL expansion
            self.config.container_item_links_item,
            context={"id": id_, "pid_value": id_, "key": key},
        )

    def file_links_item_tpl(self, id_):
        """Return a link template for item results."""
        return LinksTemplate(
            # Until all modules have transitioned to using invenio_url_for,
            # we have to keep `id` in context for URL expansion
            self.config.file_links_item,
            context={"id": id_, "pid_value": id_},
        )

    def check_permission(self, identity, action_name, **kwargs):
        """Check a permission against the identity."""
        action_name = self.config.permission_action_prefix + action_name
        return super().check_permission(identity, action_name, **kwargs)

    def _get_record(self, id_, identity, action, file_key=None, **kwargs):
        """Get the associated record.

        If a ``file_key`` is specified and the record in question doesn't have a file
        for that key, a ``FileKeyNotFoundError`` will be raised.
        """
        # FIXME: Remove "registered_only=False" since it breaks access to an
        # unpublished record.
        record = self.record_cls.pid.resolve(id_, registered_only=False)

        # note: we check file existence before checking permissions, as permission
        # checks may require the file to exist (e.g. IfTransferType permission)
        # and if it does not exist, will return a permission denied, resulting in 403
        # status code. By reveresing the order, we can return a more specific
        # 404 status code.
        if file_key and file_key not in record.files:
            raise FileKeyNotFoundError(id_, file_key)

        self.require_permission(
            identity, action, record=record, file_key=file_key, **kwargs
        )

        return record

    #
    # High-level API
    #
    def list_files(self, identity, id_, **kwargs):
        """List the files of a record."""
        record = self._get_record(id_, identity, "read_files", **kwargs)

        return self._list_files_result(identity, id_, record)

    def read_archive(self, identity, id_):
        """List a record's files for the archive download endpoint.

        Same as ``list_files`` but rejects records whose total file size
        exceeds ``RECORDS_RESOURCES_ARCHIVE_DOWNLOAD_MAX_SIZE``.
        """
        record = self._get_record(id_, identity, "read_files")
        max_size = current_app.config.get("RECORDS_RESOURCES_ARCHIVE_DOWNLOAD_MAX_SIZE")
        if (
            max_size is not None
            and record.files.enabled
            and record.files.total_bytes > max_size
        ):
            raise ArchiveDownloadTooLargeException(max_size)
        return self._list_files_result(identity, id_, record)

    def _list_files_result(self, identity, id_, record):
        self.run_components("list_files", id_, identity, record)

        return self.file_result_list(
            self,
            identity,
            results=record.files.values(),
            record=record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def init_files(self, identity, id_, data, uow=None, **kwargs):
        """Initialize the file upload for the record."""
        # validate the input data at the beginning, as we need to check
        # if user has permission for the transfer type that is on
        # each of the uploaded files. This is done in the IfTransferType
        # permission generator.
        schema = self.initial_file_schema.schema(many=True)
        data = schema.load(data)

        if not data:
            raise ValidationError("No files to upload.")

        # resolve the record and check permissions for each uploaded file
        record = self.record_cls.pid.resolve(id_, registered_only=False)

        for created_file in data:
            self.require_permission(
                identity,
                "create_files",
                record=record,
                file_metadata=created_file,
                **kwargs,
            )

        self.run_components("init_files", identity, id_, record, data, uow=uow)

        return self.file_result_list(
            self,
            identity,
            results=record.files.values(),
            record=record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def update_file_metadata(self, identity, id_, file_key, data, uow=None, **kwargs):
        """Update the metadata of a file.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(
            id_, identity, "create_files", file_key=file_key, data=data, **kwargs
        )

        self.run_components(
            "update_file_metadata", identity, id_, file_key, record, data, uow=uow
        )

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def read_file_metadata(self, identity, id_, file_key, **kwargs):
        """Read the metadata of a file.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(
            id_, identity, "read_files", file_key=file_key, **kwargs
        )

        self.run_components("read_file_metadata", identity, id_, file_key, record)

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def extract_file_metadata(self, identity, id_, file_key, uow=None, **kwargs):
        """Extract metadata from a file and update the file metadata file.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(
            id_, identity, "create_files", file_key=file_key, **kwargs
        )
        file_record = record.files[file_key]

        self.run_components(
            "extract_file_metadata",
            identity,
            id_,
            file_key,
            record,
            file_record,
            uow=uow,
        )

        uow.register(RecordCommitOp(file_record))

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def commit_file(self, identity, id_, file_key, uow=None, **kwargs):
        """Commit a file upload.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(
            id_, identity, "commit_files", file_key=file_key, **kwargs
        )

        self.run_components("commit_file", identity, id_, file_key, record, uow=uow)

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def delete_file(self, identity, id_, file_key, uow=None, **kwargs):
        """Delete a single file.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(
            id_, identity, "delete_files", file_key=file_key, **kwargs
        )
        deleted_file = record.files.delete(file_key, remove_rf=True)

        self.run_components(
            "delete_file", identity, id_, file_key, record, deleted_file, uow=uow
        )

        # We also commit the record in case the file was the `default_preview`
        uow.register(RecordCommitOp(record))

        return self.file_result_item(
            self,
            identity,
            deleted_file,
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def delete_all_files(self, identity, id_, uow=None, **kwargs):
        """Delete all the files of the record."""
        record = self._get_record(id_, identity, "delete_files", **kwargs)

        # We have to separate the gathering of the keys from their deletion
        # because of how record.files is implemented.
        file_keys = [fk for fk in record.files]
        results = [record.files.delete(file_key) for file_key in file_keys]

        self.run_components("delete_all_files", identity, id_, record, results, uow=uow)

        uow.register(RecordCommitOp(record))

        return self.file_result_list(
            self,
            identity,
            results,
            record,
            links_tpl=self.file_links_list_tpl(id_),
            links_item_tpl=self.file_links_item_tpl(id_),
        )

    @unit_of_work()
    def set_file_content(
        self, identity, id_, file_key, stream, content_length=None, uow=None, **kwargs
    ):
        """Save file content.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(
            id_,
            identity,
            "set_content_files",
            file_key=file_key,
            stream=stream,
            content_length=content_length,
            **kwargs,
        )
        errors = None
        try:
            self.run_components(
                "set_file_content",
                identity,
                id_,
                file_key,
                stream,
                content_length,
                record,
                uow=uow,
            )
            file = record.files[file_key]

        except FailedFileUploadException as e:
            file = e.file
            current_app.logger.exception("File upload transfer failed.")
            # we gracefully fail so that uow can commit the cleanup operation in
            # FileContentComponent
            errors = _("File upload transfer failed.")

        return self.file_result_item(
            self,
            identity,
            file,
            record,
            errors=errors,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def get_file_content(self, identity, id_, file_key, **kwargs):
        """Retrieve file content.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(
            id_, identity, "get_content_files", file_key=file_key, **kwargs
        )

        self.run_components("get_file_content", identity, id_, file_key, record)

        return self.file_result_item(
            self,
            identity,
            record.files[file_key],
            record,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def get_transfer_metadata(self, identity, id_, file_key):
        """Retrieve file transfer metadata."""
        record = self._get_record(
            id_, identity, "get_file_transfer_metadata", file_key=file_key
        )
        file = record.files[file_key]
        transfer_metadata = dict(file.transfer)
        self.run_components(
            "get_transfer_metadata", identity, id_, file_key, record, transfer_metadata
        )
        return transfer_metadata

    @unit_of_work()
    def update_transfer_metadata(
        self, identity, id_, file_key, transfer_metadata, uow=None
    ):
        """Update file transfer metadata."""
        record = self._get_record(
            id_, identity, "update_file_transfer_metadata", file_key=file_key
        )
        self.run_components(
            "update_transfer_metadata",
            identity,
            id_,
            file_key,
            record,
            transfer_metadata,
            uow=uow,
        )

    @unit_of_work()
    def set_multipart_file_content(
        self, identity, id_, file_key, part, stream, content_length=None, uow=None
    ):
        """Save file content of a single part.

        :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        """
        record = self._get_record(id_, identity, "set_content_files", file_key=file_key)
        errors = None
        try:
            self.run_components(
                "set_multipart_file_content",
                identity,
                id_,
                file_key,
                part,
                stream,
                content_length,
                record,
                uow=uow,
            )
            file = record.files[file_key]

        except FailedFileUploadException as e:
            file = e.file
            current_app.logger.exception("File upload transfer failed.")
            # we gracefully fail so that uow can commit the cleanup operation in
            # FileContentComponent
            errors = "File upload transfer failed."

        return self.file_result_item(
            self,
            identity,
            file,
            record,
            errors=errors,
            links_tpl=self.file_links_item_tpl(id_),
        )

    def list_container(self, identity, id_, file_key):
        """List the files in the container of a record."""
        record = self._get_record(id_, identity, "get_content_files", file_key=file_key)
        file_record = record.files[file_key]
        status = current_transfer_registry.get_transfer(
            file_record=file_record,
            file_service=self,
            record=record,
        ).status
        if status != TransferStatus.COMPLETED:
            raise FileKeyNotFoundError(id_, file_key)

        for e in self.config.file_extractors:
            if e.can_process(file_record):
                listing = e.list(file_record)
                return self.file_result_container_list(
                    self,
                    identity,
                    listing,
                    self.container_item_links_list_tpl(id_, file_key),
                )
        else:
            raise NoExtractorFoundError(file_key)

    def extract_container_item(self, identity, id_, file_key, path):
        """Extract a specific file or directory from the container of a record."""
        container_stream, record, file_record = self._open_container_item(
            identity, id_, file_key, path
        )
        return self.file_result_container_item(
            self,
            identity,
            record,
            file_record,
            container_stream,
            path,
            mimetype=getattr(container_stream, "mimetype", None),
            size=getattr(container_stream, "size", None),
        )

    def open_container_item(self, identity, id_, file_key, path):
        """Open a specific file from the container of a record."""
        return self._open_container_item(identity, id_, file_key, path)[0]

    def _open_container_item(self, identity, id_, file_key, path):
        """Open a specific file from the container of a record."""
        record = self._get_record(id_, identity, "get_content_files", file_key=file_key)
        file_record = record.files[file_key]
        status = current_transfer_registry.get_transfer(
            file_record=file_record,
            file_service=self,
            record=record,
        ).status
        if status != TransferStatus.COMPLETED:
            raise FileKeyNotFoundError(id_, file_key)

        for e in self.config.file_extractors:
            if e.can_process(file_record):
                return e.open(file_record, path), record, file_record
        else:
            raise NoExtractorFoundError(file_key)
