# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service API."""

from ..errors import PermissionDeniedError


class Service:
    """Service interface.

    A service requires a service configuration. Several ways exist to provide
    the config.

    1. Injection via constructor
    2. Loading from Flask application config (see ``config_name``).
    3. Default config set as class attribute on service class (see
       ``default_config``).
    """

    def __init__(self, config):
        """Constructor.

        :param config: A service configuration
        """
        self.config = config

    #
    # Permissions checking
    #
    def permission_policy(self, action_name, **kwargs):
        """Factory for a permission policy instance."""
        return self.config.permission_policy_cls(action_name, **kwargs)

    def check_permission(self, identity, action_name, **kwargs):
        """Check a permission against the identity."""
        return self.permission_policy(action_name, **kwargs).allows(identity)

    def require_permission(self, identity, action_name, **kwargs):
        """Require a specific permission from the permission policy.

        Like `check_permission` but raises an error if not allowed.
        """
        if not self.check_permission(identity, action_name, **kwargs):
            raise PermissionDeniedError(action_name)

    #
    # Units of transaction methods (creation...)
    #
    def result_item(self, *args, **kwargs):
        """Create a new instance of the resource unit.

        A resource unit is an instantiated object representing one unit
        of a Resource. It is what a Resource transacts in and therefore
        what a Service must provide.
        """
        return self.config.result_item_cls(*args, **kwargs)

    def result_list(self, *args, **kwargs):
        """Create a new instance of the resource list.

        A resource list is an instantiated object representing a grouping
        of Resource units. Sometimes this group has additional data making
        a simple iterable of resource units inappropriate. It is what a
        Resource list methods transact in and therefore what
        a Service must provide.
        """
        return self.config.result_list_cls(*args, **kwargs)
