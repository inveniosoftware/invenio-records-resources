# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 - 2022 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resolver and proxy for users."""


from flask_principal import UserNeed
from invenio_accounts.models import User

from .base import EntityProxy, EntityResolver


class UserProxy(EntityProxy):
    """Resolver proxy for a User entity."""

    def _resolve(self):
        """Resolve the User from the proxy's reference dict."""
        user_id = int(self._parse_ref_dict_id(self._ref_dict))
        return User.query.get(user_id)

    def get_needs(self, ctx=None):
        """Get the UserNeed for the referenced user."""
        user_id = int(self._parse_ref_dict_id(self._ref_dict))
        return [UserNeed(user_id)]


class UserResolver(EntityResolver):
    """Resolver for users."""

    type_id = 'user'

    def matches_reference_dict(self, ref_dict):
        """Check if the reference dict references a user."""
        return self._parse_ref_dict_type(ref_dict) == self.type_id

    def _reference_entity(self, entity):
        """Create a reference dict for the given user."""
        return {"user": str(entity.id)}

    def matches_entity(self, entity):
        """Check if the entity is a user."""
        return isinstance(entity, User)

    def _get_entity_proxy(self, ref_dict):
        """Return a UserProxy for the given reference dict."""
        return UserProxy(ref_dict)
