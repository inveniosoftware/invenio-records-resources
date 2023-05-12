# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 - 2022 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Registry for easy access to the registered entity resolvers."""

from abc import ABC, abstractmethod

from invenio_access.permissions import system_identity, system_user_id


class ResolverRegistryBase(ABC):
    """Base class for a resolver registry."""

    @classmethod
    @abstractmethod
    def get_registered_resolvers(cls):
        """Get all currently registered resolvers."""
        raise NotImplementedError()

    @classmethod
    def resolve_entity_proxy(cls, reference_dict, raise_=False):
        """Get a proxy for the referenced entity via the configured resolvers.

        If ``REQUESTS_ENTITY_RESOLVERS`` does not contain a matching
        EntityResolver for the given ``reference_dict``, the ``raise_``
        parameter determines whether a ``ValueError`` is raised or
        ``None`` is returned.
        """
        for resolver in cls.get_registered_resolvers():
            if resolver.matches_reference_dict(reference_dict):
                return resolver.get_entity_proxy(reference_dict, check=False)

        if raise_:
            msg = f"No matching resolver registered for: {reference_dict}"
            raise ValueError(msg)

        return None

    @classmethod
    def resolve_entity(cls, reference_dict, raise_=False):
        """Resolve the referenced entity via the configured resolvers.

        This calls ``resolve_entity_proxy()`` and then ``resolve()`` on
        the proxy.
        Note that this may create an expensive lookup, like a DB query.
        """
        proxy = cls.resolve_entity_proxy(reference_dict, raise_=raise_)

        if proxy is None:
            return None

        return proxy.resolve()

    @classmethod
    def resolve_need(cls, reference_dict, raise_=False, ctx=None):
        """Get the need for the referenced entity via the configured resolvers.

        This calls ``resolve_entity_proxy()`` and then ``get_needs()`` on
        the proxy.
        Note: If the concept of needs is not applicable to the referenced
        type of entity (e.g. ``Request``), ``None`` is returned.
        """
        proxy = cls.resolve_entity_proxy(reference_dict, raise_=raise_)

        if proxy is None:
            return None

        return proxy.get_needs(ctx=ctx)

    @classmethod
    def reference_entity(cls, entity, raise_=False):
        """Create a reference dict for the entity via the configured resolvers.

        If ``REQUESTS_ENTITY_RESOLVERS`` does not contain a matching
        EntityResolver for the given ``entity``, the ``raise_`` parameter
        determines whether a ``ValueError`` is raised or ``None`` is returned.
        """
        for resolver in cls.get_registered_resolvers():
            try:
                if resolver.matches_entity(entity):
                    return resolver.reference_entity(entity, check=False)
                elif isinstance(entity, dict) and resolver.matches_reference_dict(
                    entity
                ):
                    return entity
            except ValueError:
                # Value error ignored from matches_reference_dict
                pass

        if raise_:
            msg = f"No matching resolver registered for: {type(entity)}"
            raise ValueError(msg)

        return None

    @classmethod
    def reference_identity(cls, identity, raise_=False):
        """Create a reference dict for the user behind the given identity."""
        if identity == system_identity:
            return {"user": str(system_user_id)}

        return {"user": str(identity.id)}
