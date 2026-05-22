# SPDX-FileCopyrightText: 2021-2024 CERN.
# SPDX-FileCopyrightText: 2025 CESNET.
# SPDX-License-Identifier: MIT

"""Transfer providers."""

from .fetch import FetchTransfer
from .local import LocalTransfer
from .multipart import MultipartTransfer
from .remote import RemoteTransfer, RemoteTransferBase

__all__ = (
    "RemoteTransferBase",
    "RemoteTransfer",
    "LocalTransfer",
    "FetchTransfer",
    "MultipartTransfer",
)
