# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resolver for result items."""

from invenio_access.permissions import system_identity

from .base import EntityProxy, EntityResolver


class ServiceResultProxy(EntityProxy):
    """Resolver proxy for a result item entity."""

    def __init__(self, resolver, ref_dict, service):
        """Constructor."""
        super().__init__(resolver, ref_dict)
        self.service = service

    def _resolve(self):
        """Resolve the result item from the proxy's reference dict."""
        id_ = self._parse_ref_dict_id()
        # TODO: Make identity customizable
        return self.service.read(system_identity, id_).to_dict()

    def get_needs(self, ctx=None):
        """Return needs."""
        return []

    def pick_resolved_fields(self, identity, resolved_dict):
        """Select which fields to return when resolving the reference."""
        return {"id": resolved_dict["id"]}


class ServiceResultResolver(EntityResolver):
    """Resolver for result items."""

    def __init__(
        self,
        service_id,
        type_key,
        proxy_cls=ServiceResultProxy,
        item_cls=None,
        record_cls=None,
    ):
        """Constructor.

        :param item_cls: The result item class to use.
        :param service_id: The record service id.
        :param type_key: The value to use for the TYPE part of the ref_dicts.
        """
        super().__init__(service_id)
        self.type_key = type_key
        self.proxy_cls = proxy_cls
        self._item_cls = item_cls
        self._record_cls = record_cls

    @property
    def item_cls(self):
        """Get specified item class or from service."""
        return self._item_cls or self.get_service().config.result_item_cls

    @property
    def record_cls(self):
        """Get specified record class or from service."""
        return self._record_cls or self.get_service().record_cls

    def matches_entity(self, entity):
        """Check if the entity is a result item."""
        return isinstance(entity, (self.item_cls, self.record_cls))

    def _reference_entity(self, entity):
        """Create a reference dict for the given result item."""
        return {self.type_key: str(entity.id)}

    def matches_reference_dict(self, ref_dict):
        """Check if the reference dict references a request."""
        return self._parse_ref_dict_type(ref_dict) == self.type_key

    def _get_entity_proxy(self, ref_dict):
        """Return a ResultItemProxy for the given reference dict."""
        return self.proxy_cls(self, ref_dict, service=self.get_service())
