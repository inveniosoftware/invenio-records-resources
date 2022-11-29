# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 - 2022 TU Wien.
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resolver for records."""

from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound

from .base import EntityProxy, EntityResolver


class RecordProxy(EntityProxy):
    """Resolver proxy for a Record entity using the pid."""

    def __init__(self, resolver, ref_dict, record_cls):
        """Constructor.

        :param record_cls: The record class to use.
        """
        super().__init__(resolver, ref_dict)
        self.record_cls = record_cls

    def _resolve(self):
        """Resolve the Record from the proxy's reference dict."""
        pid_value = self._parse_ref_dict_id()
        return self.record_cls.pid.resolve(pid_value)

    def get_needs(self, ctx=None):
        """Return None since Needs are not applicable to records."""
        return []

    def pick_resolved_fields(self, identity, resolved_dict):
        """Select which fields to return when resolving the reference."""
        return {"id": resolved_dict["id"]}


class RecordPKProxy(RecordProxy):
    """Resolver proxy for a Record entity using the UUID."""

    def _resolve(self):
        """Resolve the Record from the proxy's reference dict."""
        id_ = self._parse_ref_dict_id()
        try:
            return self.record_cls.get_record(id_)
        except StatementError as exc:
            raise NoResultFound() from exc


class RecordResolver(EntityResolver):
    """Resolver for records."""

    def __init__(
        self, record_cls, service_id, type_key="record", proxy_cls=RecordProxy
    ):
        """Constructor.

        :param record_cls: The record class to use.
        :param service_id: The record service id.
        :param type_key: The value to use for the TYPE part of the ref_dicts.
        """
        self.record_cls = record_cls
        self.type_key = type_key
        self.proxy_cls = proxy_cls
        super().__init__(service_id)

    def matches_entity(self, entity):
        """Check if the entity is a record."""
        return isinstance(entity, self.record_cls)

    def _reference_entity(self, entity):
        """Create a reference dict for the given record."""
        return {self.type_key: str(entity.pid.pid_value)}

    def matches_reference_dict(self, ref_dict):
        """Check if the reference dict references a request."""
        return self._parse_ref_dict_type(ref_dict) == self.type_key

    def _get_entity_proxy(self, ref_dict):
        """Return a RecordProxy for the given reference dict."""
        return self.proxy_cls(self, ref_dict, self.record_cls)
