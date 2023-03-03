# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 - 2022 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Base class for entity resolvers."""

from abc import ABC, abstractmethod

from invenio_records_resources.proxies import current_service_registry


def _parse_ref_dict(reference_dict, strict=True):
    """Parse the referenced dict into a tuple (TYPE, ID).

    The ``strict`` parameter controls if the number of keys in the
    reference dict is checked strictly or not.
    """
    keys = list(reference_dict.keys())

    if strict and len(keys) != 1:
        raise ValueError(
            "Reference dicts may only have one property! "
            f"Offending dict: {reference_dict}"
        )

    if not keys:
        return None

    type_ = keys[0]
    id_ = reference_dict[type_]
    return (type_, id_)


class EntityProxy(ABC):
    """Proxy for a type of entity which only resolves the entity if requested.

    EntityProxies are responsible for resolving the entities referenced in
    the reference dicts, and thus act as another layer of abstraction.
    They provide a unified interface for resolving the actual entities from
    the dicts, or creating Needs from the references (which is useful for
    permission checks, for instance on owners of records or requests).
    Also, they enable the actual entity to be lazily loaded via the explicit
    ``resolve()`` operation, which prevents unnecessary lookups if the entity
    is not of importance (e.g. when only the Need is relevant).
    After the first lookup, the resolved entity will be cached by the proxy
    object.
    """

    def __init__(self, resolver, reference_dict):
        """Constructor."""
        self._resolver = resolver
        self._ref_dict = reference_dict
        self._entity = None

    def __repr__(self):
        """Return repr(self)."""
        return f"<{type(self).__name__} {self._ref_dict} ({self._entity})>"

    def _parse_ref_dict(self):
        """Parse the referenced dict into a tuple (TYPE, ID)."""
        return _parse_ref_dict(self._ref_dict)

    def _parse_ref_dict_type(self):
        """Parse the TYPE from the reference dict."""
        return _parse_ref_dict(self._ref_dict)[0]

    def _parse_ref_dict_id(self):
        """Parse the ID from the reference dict."""
        return _parse_ref_dict(self._ref_dict)[1]

    @property
    def reference_dict(self):
        """Get the proxy's reference dict."""
        return self._ref_dict

    def resolve(self):
        """Resolve the referenced entity via a query."""
        if self._entity is not None:
            # caching
            return self._entity

        self._entity = self._resolve()
        return self._entity

    @abstractmethod
    def _resolve(self):
        """The logic for performing the actual resolve operation.

        This method must be implemented by concrete subclasses.
        Note: The caching logic is already handled in ``resolve()``,
        so this method should contain the pure resolution logic.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_needs(self, ctx=None):
        """Get the Need for the referenced entity, if applicable.

        If the concept is not applicable for this resolver's type of entities,
        ``[]`` will be returned.
        """
        raise NotImplementedError()

    def get_resolver(self):
        """Get the concrete resolver obj used to resolve the entity."""
        return self._resolver

    @abstractmethod
    def pick_resolved_fields(self, identity, resolved_dict):
        """Select which fields to return when resolving the reference."""
        raise NotImplementedError()


class EntityResolver(ABC):
    """Translation layer between reference dicts and entities (or proxies).

    The resolvers are a layer of abstraction between the reference dicts and
    their referenced entities.
    They are directly responsible for handling the reference dumping direction
    themselves (i.e. creating reference dicts from entities), while the other
    direction (i.e. resolving entities from reference dicts) is the
    responsibility of the EntityProxies created by the resolvers.
    """

    def __init__(self, service_id):
        """Constructor.

        :params service: the service for the record to resolve.
        """
        self._service_id = service_id

    def _parse_ref_dict(self, ref_dict):
        """Parse the referenced dict into a tuple (TYPE, ID)."""
        return _parse_ref_dict(ref_dict)

    def _parse_ref_dict_type(self, ref_dict):
        """Parse the TYPE from the reference dict."""
        return self._parse_ref_dict(ref_dict)[0]

    def _parse_ref_dict_id(self, ref_dict):
        """Parse the ID from the reference dict."""
        return self._parse_ref_dict(ref_dict)[1]

    def get_entity_proxy(self, ref_dict, check=True):
        """Check compatibility and get a proxy for the referenced entity.

        This method will optionally check the shape of the given reference
        dict via ``matches_reference_dict()`` before creating a proxy via
        ``_get_entity_proxy()``.
        If this check fails, a ``ValueError`` will be raised.
        """
        if check and not self.matches_reference_dict(ref_dict):
            raise ValueError(
                f"{type(self).__name__} cannot handle "
                f"the following reference dict: {ref_dict}"
            )

        return self._get_entity_proxy(ref_dict)

    def reference_entity(self, entity, check=True):
        """Check compatibility and create a reference dict for the entity.

        This method will perform an optional instance check of the given
        entity via ``matches_entity()`` before dumping a reference via
        ``_reference_entity()``.
        If this check fails, a ``ValueError`` will be raised.
        """
        if check and not self.matches_entity(entity):
            raise ValueError(
                f"{type(self).__name__} cannot handle "
                f"the following entity: {entity}"
            )

        return self._reference_entity(entity)

    @abstractmethod
    def matches_reference_dict(self, ref_dict):
        """Check if the ref_dict matches the expectations of this resolver."""
        raise NotImplementedError()

    @abstractmethod
    def matches_entity(self, entity):
        """Check if the entity matches the expectations of this resolver."""
        raise NotImplementedError()

    @abstractmethod
    def _get_entity_proxy(self, ref_dict):
        """The logic for building a proxy for the referenced entity.

        Since the compatibility checks are already taken care of, this
        method can assume that the data is valid and can focus on simply
        creating the proxy for the referenced entity.

        Example:
            return EntityProxy(self, ref_dict)
        """
        raise NotImplementedError()

    @abstractmethod
    def _reference_entity(self, entity):
        """The logic building a reference dict from the given entity.

        Since the compatibility checks are already taken care of, this method
        can assume that the entity is compatible and can focus on simply
        creating the reference dict for the given entity.

        Example:
            return {self.type_key: entity.id}
        """
        raise NotImplementedError()

    def get_service(self):
        """Return the record service."""
        return current_service_registry.get(self._service_id)
