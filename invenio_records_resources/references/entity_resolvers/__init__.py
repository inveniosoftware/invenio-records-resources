# SPDX-FileCopyrightText: 2021-2022 TU Wien.
# SPDX-License-Identifier: MIT

"""Default entity resolvers and proxies."""

from .base import EntityProxy, EntityResolver
from .records import RecordPKProxy, RecordProxy, RecordResolver
from .results import ServiceResultProxy, ServiceResultResolver

__all__ = (
    "EntityProxy",
    "EntityResolver",
    "RecordPKProxy",
    "RecordProxy",
    "RecordResolver",
    "ServiceResultProxy",
    "ServiceResultResolver",
)
