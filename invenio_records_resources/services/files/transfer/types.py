import dataclasses


@dataclasses.dataclass(frozen=True)
class TransferType:
    type: str
    is_serializable: bool


# predefined transfer types
LOCAL_TRANSFER_TYPE = TransferType(type="L", is_serializable=False)
FETCH_TRANSFER_TYPE = TransferType(type="F", is_serializable=True)
REMOTE_TRANSFER_TYPE = TransferType(type="R", is_serializable=True)
