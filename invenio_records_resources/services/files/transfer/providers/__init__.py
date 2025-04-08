# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
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
