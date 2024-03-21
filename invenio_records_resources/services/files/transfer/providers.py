from invenio_records_resources.records import FileRecord

from ...errors import TransferException
from ...uow import TaskOp
from ..tasks import fetch_file
from .base import BaseTransfer, TransferStatus
from .types import FETCH_TRANSFER_TYPE, LOCAL_TRANSFER_TYPE


class LocalTransfer(BaseTransfer):
    """Local transfer."""

    transfer_type = LOCAL_TRANSFER_TYPE

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

    def init_file(self, record, file_metadata):
        """Initialize a file."""
        uri = file_metadata.pop("uri", None)
        if uri:
            raise Exception("Cannot set URI for local files.")

        file = record.files.create(key=file_metadata.pop("key"), data=file_metadata)

        return file

    def set_file_content(self, record, file, file_key, stream, content_length):
        """Set file content."""
        if file:
            raise TransferException(f'File with key "{file_key}" is committed.')

        super().set_file_content(record, file, file_key, stream, content_length)


class FetchTransfer(BaseTransfer):
    """Fetch transfer."""

    transfer_type = FETCH_TRANSFER_TYPE

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

    def init_file(self, record, file_metadata):
        """Initialize a file."""
        uri = file_metadata.pop("uri", None)
        if not uri:
            raise Exception("URI is required for fetch files.")

        obj_kwargs = {
            "file": {
                "uri": uri,
                "storage_class": self.transfer_type.type,
                "checksum": file_metadata.pop("checksum", None),
                "size": file_metadata.pop("size", None),
            }
        }

        file_key = file_metadata.pop("key")
        file = record.files.create(
            key=file_key,
            data=file_metadata,
            obj=obj_kwargs,
        )

        self.uow.register(
            TaskOp(
                fetch_file,
                service_id=self.service.id,
                record_id=record.pid.pid_value,
                file_key=file_key,
            )
        )
        return file
