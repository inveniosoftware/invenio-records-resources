# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files transfer."""


from .base import BaseTransfer
from .providers import FetchTransfer, LocalTransfer
from .types import (
    FETCH_TRANSFER_TYPE,
    LOCAL_TRANSFER_TYPE,
    REMOTE_TRANSFER_TYPE,
)

__all__ = (
    "BaseTransfer",
    "LocalTransfer",
    "FetchTransfer",
    "LOCAL_TRANSFER_TYPE",
    "FETCH_TRANSFER_TYPE",
    "REMOTE_TRANSFER_TYPE",
)
