from typing import Dict, Type

from invenio_records_resources.services.files.transfer import TransferType
from invenio_records_resources.services.files.transfer.base import BaseTransfer


class TransferRegistry:
    """
    A registry for transfer providers.
    """

    DEFAULT_TRANSFER_TYPE = "L"
    """
    Default transfer type if no storage class is provided in file upload initiation.
    """

    def __init__(self):
        self._transfers: Dict[str, Type[BaseTransfer]] = {}

    def register(self, transfer_cls: Type[BaseTransfer]):
        """Register a new transfer provider."""

        transfer_type = transfer_cls.transfer_type.type

        if transfer_type in self._transfers:
            raise RuntimeError(
                f"Transfer with type '{transfer_type}' " "is already registered."
            )

        self._transfers[transfer_type] = transfer_cls

    def get_transfer(self, transfer_type, **kwargs):
        """Get transfer type."""
        if transfer_type is None:
            transfer_type = self.DEFAULT_TRANSFER_TYPE

        if isinstance(transfer_type, TransferType):
            transfer_type = transfer_type.type

        return self._transfers[transfer_type](**kwargs)
