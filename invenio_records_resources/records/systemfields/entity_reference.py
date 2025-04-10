# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 - 2022 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Systemfield for managing referenced entities in request."""


from invenio_records.systemfields import SystemField

from ...references.entity_resolvers import EntityProxy


class ReferencedEntityField(SystemField):
    """Systemfield for managing the request type."""

    def __init__(self, key=None, reference_check_func=None, resolver_registry=None):
        """Constructor."""
        super().__init__(key=key)
        self._ref_check = reference_check_func
        self._registry = resolver_registry

    def _check_reference(self, instance, ref_dict):
        """Check if the reference is accepted."""
        if self._ref_check is None:
            return True

        return self._ref_check(instance, ref_dict)

    def set_obj(self, instance, obj):
        """Set the referenced entity."""
        # allow the setter to be used with a reference dict,
        # an entity proxy, or an actual entity
        if not isinstance(obj, dict):
            if isinstance(obj, EntityProxy):
                obj = obj.reference_dict
            elif obj is not None:
                obj = self._registry.reference_entity(obj, raise_=True)

        # check if the reference is allowed
        if not self._check_reference(instance, obj):
            raise ValueError(
                _("Invalid reference for '%(key)s': %(obj)s", key=self.key, obj=obj)
            )

        # set dictionary key and reset the cache
        self.set_dictkey(instance, obj)
        self._set_cache(instance, None)

    def __set__(self, record, value):
        """Set the referenced entity."""
        assert record is not None
        self.set_obj(record, value)

    def obj(self, instance):
        """Get the referenced entity as an ``EntityProxy``."""
        obj = self._get_cache(instance)
        if obj is not None:
            return obj

        reference_dict = self.get_dictkey(instance)
        if reference_dict is None:
            # TODO maybe use a `NullProxy` instead?
            return None

        obj = self._registry.resolve_entity_proxy(reference_dict)
        self._set_cache(instance, obj)
        return obj

    def __get__(self, record, owner=None):
        """Get the referenced entity as an ``EntityProxy``."""
        if record is None:
            # access by class
            return self

        return self.obj(record)


class MultiReferenceEntityField(ReferencedEntityField):
    """System field extending ReferencedEntityField to support object lists."""

    def set_obj(self, instance, objs):
        """Set multiple referenced entities."""
        references = []

        for obj in objs:
            if isinstance(obj, dict):
                ref_dict = obj
            elif isinstance(obj, EntityProxy):
                ref_dict = obj.reference_dict
            elif obj is not None:
                ref_dict = self._registry.reference_entity(obj, raise_=True)
            else:
                continue

            if not self._check_reference(instance, ref_dict):
                raise ValueError(f"Invalid reference for '{self.key}': {ref_dict}")

            references.append(ref_dict)

        self.set_dictkey(instance, references)
        self._set_cache(instance, None)

    def obj(self, instance):
        """Get the referenced entities as a list of `EntityProxy` objects."""
        cached = self._get_cache(instance)
        if cached is not None:
            return cached

        references_list = self.get_dictkey(instance)
        if references_list is None:
            return []

        resolved_objects = [
            self._registry.resolve_entity_proxy(ref_dict)
            for ref_dict in references_list
        ]

        self._set_cache(instance, resolved_objects)
        return resolved_objects


def check_allowed_references(get_allows_none, get_allowed_types, request, ref_dict):
    """Check the reference according to rules specific to requests.

    In case the ``ref_dict`` is ``None``, it will check if this is allowed
    for the reference at hand.
    Otherwise, it will check if the reference dict's key (i.e. the TYPE)
    is allowed.
    """
    if ref_dict is None:
        return get_allows_none(request)

    if not len(ref_dict) == 1:
        # we expect a ref_dict to have the shape {"TYPE": "ID"}
        return False

    ref_type = list(ref_dict.keys())[0]
    return ref_type in get_allowed_types(request)
