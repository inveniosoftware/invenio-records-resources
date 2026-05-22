# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-FileCopyrightText: 2025 CESNET.
# SPDX-License-Identifier: MIT

"""Files transfer."""

from .base import Transfer, TransferStatus
from .constants import (
    FETCH_TRANSFER_TYPE,
    LOCAL_TRANSFER_TYPE,
    MULTIPART_TRANSFER_TYPE,
    REMOTE_TRANSFER_TYPE,
)
from .providers.fetch import FetchTransfer
from .providers.local import LocalTransfer
from .providers.multipart import MultipartTransfer
from .providers.remote import RemoteTransfer

__all__ = (
    "Transfer",
    "FETCH_TRANSFER_TYPE",
    "LOCAL_TRANSFER_TYPE",
    "MULTIPART_TRANSFER_TYPE",
    "REMOTE_TRANSFER_TYPE",
    "TransferStatus",
    "FetchTransfer",
    "LocalTransfer",
    "MultipartTransfer",
    "RemoteTransfer",
)
