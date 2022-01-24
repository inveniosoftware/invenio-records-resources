# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 - 2022 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module for entity resolvers."""

from .registry import ResolverRegistryBase
from .resolvers import EntityResolver, RecordResolver, UserResolver

__all__ = (
    "EntityResolver",
    "RecordResolver",
    "ResolverRegistryBase",
    "UserResolver",
)
