# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service API."""

from invenio_records_permissions.policies import BasePermissionPolicy

from .errors import PermissionDeniedError


class ServiceConfig:
    """Service Configuration."""

    # Common configuration for all Services
    permission_policy_cls = BasePermissionPolicy
    resource_unit_cls = dict
    resource_list_cls = list


class Service:
    """Service interface."""

    default_config = ServiceConfig

    def __init__(self, config=None):
        """Constructor."""
        self.config = config or self.default_config

    #
    # Permissions checking
    #
    def permission_policy(self, action_name, **kwargs):
        """Factory for a permission policy instance."""
        return self.config.permission_policy_cls(action_name, **kwargs)

    def require_permission(self, identity, action_name, **kwargs):
        """Require a specific permission from the permission policy."""
        if not self.permission_policy(action_name, **kwargs).allows(identity):
            raise PermissionDeniedError(action_name)

    #
    # Units of transaction methods (creation...)
    #
    def resource_unit(self, *args, **kwargs):
        """Create a new instance of the resource unit.

        A resource unit is an instantiated object representing one unit
        of a Resource. It is what a Resource transacts in and therefore
        what a Service must provide.
        """
        return self.config.resource_unit_cls(*args, **kwargs)

    def resource_list(self, *args, **kwargs):
        """Create a new instance of the resource list.

        A resource list is an instantiated object representing a grouping
        of Resource units. Sometimes this group has additional data making
        a simple iterable of resource units inappropriate. It is what a
        Resource list methods transact in and therefore what
        a Service must provide.
        """
        return self.config.resource_list_cls(*args, **kwargs)
