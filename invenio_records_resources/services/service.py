# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service API."""

from invenio_base.utils import load_or_import_from_config
from invenio_records_permissions.policies import BasePermissionPolicy

from .errors import PermissionDeniedError


class ServiceConfig:
    """Service Configuration."""

    # Common configuration for all Services
    permission_policy_cls = BasePermissionPolicy
    """The permission policy class to use."""

    resource_unit_cls = dict
    resource_list_cls = list


class Service:
    """Service interface.

    A service requires a service configuration. Several ways exist to provide
    the config.

    1. Injection via constructor
    2. Loading from Flask application config (see ``config_name``).
    3. Default config set as class attribute on service class (see
       ``default_config``).
    """

    default_config = ServiceConfig
    """Default service configuration."""

    config_name = None
    """Name of Flask configuration variable.

    The variable is used to dynamically load a service configuration specified
    by the user. A concrete service subclass most overwrite this attribute.
    """

    def __init__(self, config=None):
        """Constructor.

        :param config: Provide the ser
        """
        self.config = (
            config or
            load_or_import_from_config(
                self.config_name, default=self.default_config
            )
        )

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
