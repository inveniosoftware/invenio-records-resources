# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service registry."""


class ServiceRegistry:
    """A simple class to register services."""

    def __init__(self):
        """Initialize the registry."""
        self._services = {}

    def register(self, service_instance, service_id=None):
        """Register a new service instance."""
        if service_id is None:
            service_id = service_instance.config.service_id
        if service_id in self._services:
            raise RuntimeError(
                f"Service with service id '{service_id}' "
                "is already registered."
            )
        self._services[service_id] = service_instance

    def get(self, service_id):
        """Get a service for a given service_id."""
        return self._services[service_id]

    def get_service_id(self, instance):
        """Get the service id for a specific instance."""
        for service_id, service_instance in self._services.items():
            if instance == service_instance:
                return service_id
        raise KeyError("Service not found in registry.")
