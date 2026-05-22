# SPDX-FileCopyrightText: 2021-2022 TU Wien.
# SPDX-License-Identifier: MIT

"""Module for entity resolvers."""

from .entity_resolvers import EntityResolver, RecordResolver
from .grants import EntityGrant
from .registry import ResolverRegistryBase

__all__ = (
    "EntityGrant",
    "EntityResolver",
    "RecordResolver",
    "ResolverRegistryBase",
)
