from abc import ABC, abstractmethod

from flask_babel import lazy_gettext as _
from fs.errors import CreateFailed
from invenio_files_rest.errors import FileSizeError
from werkzeug.exceptions import ClientDisconnected

from invenio_records_resources.records import Record, FileRecord
from invenio_records_resources.services.errors import TransferException


class TransferStatus:
    """Transfer status. Constants to be used as return values for get_status."""

    #  Can not be enum to be json serializable, so just a class with constants.

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseTransfer(ABC):
    """Local transfer."""

    transfer_type: str = None
    """
    The transfer type for this transfer instance.
    Overriding classes must set this attribute.
    """

    is_serializable = False
    """
    True if this transfer can be serialized, false otherwise
    """

    def __init__(self, record: Record = None, file_record: FileRecord = None, service=None, uow=None):
        """Constructor."""
        self.record = record
        self.file_record = file_record
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

    def commit_file(self):
        """Commit a file."""
        # fetch files can be committed, its up to permissions to decide by who
        # e.g. system, since its the one downloading the file
        self.record.files.commit(self.file_record.key)

    @property
    def status(self):
        """
        Get status of the upload of the passed file record.

        Returns TransferStatus.COMPLETED if the file is uploaded,
        TransferStatus.PENDING if the file is not uploaded yet or
        TransferStatus.FAILED if the file upload failed.
        """

        if self.file_record is not None and self.file_record.file is not None:
            return TransferStatus.COMPLETED

        return TransferStatus.PENDING

    @property
    def transfer_data(self):
        return {
            'status': self.status,
        }

    def expand_links(self, identity, file_record):
        """Expand links."""
        return {}

    # @abstractmethod
    # def read_file_content(self, record, file_metadata):
    #     """Read a file content."""
    #     pass
