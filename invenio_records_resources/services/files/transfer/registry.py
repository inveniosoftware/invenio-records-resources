from typing import Dict, Type

from .base import BaseTransfer
from .types import LOCAL_TRANSFER_TYPE


class TransferRegistry:
    """
    A registry for transfer providers.
    """

    DEFAULT_TRANSFER_TYPE = LOCAL_TRANSFER_TYPE
    """
    Default transfer type if no storage class is provided in file upload initiation.
    """

    def __init__(self):
        self._transfers: Dict[str, Type[BaseTransfer]] = {}

    def register(self, transfer_cls: Type[BaseTransfer]):
        """Register a new transfer provider."""

        transfer_type = transfer_cls.transfer_type

        if transfer_type in self._transfers:
            raise RuntimeError(
                f"Transfer with type '{transfer_type}' " "is already registered."
            )

        self._transfers[transfer_type] = transfer_cls

    def get_transfer(self, *, transfer_type=None, file_record=None, **kwargs):
        """Get transfer type."""

        if transfer_type is None:
            if file_record is not None and file_record.file is not None:
                transfer_type = file_record.file.storage_class

        return self._transfers[transfer_type or self.DEFAULT_TRANSFER_TYPE](
            file_record=file_record, **kwargs)
