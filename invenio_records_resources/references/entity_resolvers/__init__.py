# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 - 2022 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

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
