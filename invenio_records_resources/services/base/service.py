# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
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
    # Pluggable components
    #
    @property
    def components(self):
        """Return initialized service components."""
        return (c(self) for c in self.config.components)

    def run_components(self, action, *args, **kwargs):
        """Run components for a given action."""
        uow = kwargs.pop("uow", None)

        for component in self.components:
            if hasattr(component, action):
                # Done like this to avoid breaking API changes.
                # uow should eventually be passed directly to the component
                # so service/component method signature matches.
                if uow is not None:
                    component.uow = uow
                getattr(component, action)(*args, **kwargs)
                component.uow = None

    @property
    def id(self):
        """Return the id of the service from config."""
        return self.config.service_id

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

    def result_bulk_item(self, *args, **kwargs):
        """Create a new instance of the bulk resource unit.

        A bulk resource unit is an instantiated object representing one unit
        of a Resource. It is what a bulk Resource unit methods transact in
        and therefore what a Service must provide.
        """
        return self.config.result_bulk_item_cls(*args, **kwargs)

    def result_bulk_list(self, *args, **kwargs):
        """Create a new instance of the bulk resource list.

        A bulk resource list is an instantiated object representing a grouping
        of Resource units. It is what a bulk Resource list methods transact in
        and therefore what a Service must provide.
        """
        return self.config.result_bulk_list_cls(*args, **kwargs)
