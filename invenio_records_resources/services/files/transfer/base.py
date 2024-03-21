from abc import ABC, abstractmethod
from enum import Enum

from flask_babel import lazy_gettext as _
from fs.errors import CreateFailed
from invenio_files_rest.errors import FileSizeError
from werkzeug.exceptions import ClientDisconnected

from invenio_records_resources.proxies import current_transfer_registry
from invenio_records_resources.records import FileRecord
from invenio_records_resources.services.errors import TransferException
from invenio_records_resources.services.files.transfer.types import TransferType


class TransferStatus:
    """Transfer status. Constants to be used as return values for get_status."""

    #  Can not be enum to be json serializable, so just a class with constants.

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseTransfer(ABC):
    """Local transfer."""

    transfer_type: TransferType = None
    """
    The transfer type for this transfer instance.
    Overriding classes must set this attribute.
    """

    def __init__(self, service=None, uow=None):
        """Constructor."""
        self.service = service
        self.uow = uow

    @abstractmethod
    def init_file(self, record, file_metadata):
        """Initialize a file."""
        raise NotImplementedError()

    def set_file_content(self, record, file, file_key, stream, content_length):
        """Set file content."""
        bucket = record.bucket

        size_limit = bucket.size_limit
        if content_length and size_limit and content_length > size_limit:
            desc = (
                _("File size limit exceeded.")
                if isinstance(size_limit, int)
                else size_limit.reason
            )
            raise FileSizeError(description=desc)

        try:
            record.files.create_obj(
                file_key, stream, size=content_length, size_limit=size_limit
            )
        except (ClientDisconnected, CreateFailed) as e:
            raise TransferException(f'Transfer of File with key "{file_key}" failed.')

    def commit_file(self, record, file_key):
        """Commit a file."""
        # fetch files can be committed, its up to permissions to decide by who
        # e.g. system, since its the one downloading the file
        record.files.commit(file_key)

    def get_status(self, obj: FileRecord):
        """
        Get status of the upload of the passed file record.

        Returns TransferStatus.COMPLETED if the file is uploaded,
        TransferStatus.PENDING if the file is not uploaded yet or
        TransferStatus.FAILED if the file upload failed.
        """

        if obj.file:
            return TransferStatus.COMPLETED

        return TransferStatus.PENDING

    # @abstractmethod
    # def read_file_content(self, record, file_metadata):
    #     """Read a file content."""
    #     pass


class Transfer:
    """Transfer type."""

    @classmethod
    def get_transfer(cls, file_type, **kwargs):
        """Get transfer type."""
        return current_transfer_registry.get_transfer(file_type, **kwargs)

    @classmethod
    def commit_file(cls, record, file_key):
        """Commit a file."""
        file = record.files.get(file_key).file
        transfer = cls.get_transfer(getattr(file, "storage_class", None))
        # file is not passed since that is the current head of the OV
        # committing means setting the latest of the bucket (OV.get)
        transfer.commit_file(record, file_key)
