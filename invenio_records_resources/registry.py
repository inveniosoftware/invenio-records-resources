# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio-Records-Resources registry."""


class ServiceRegistry:
    """A simple class to register services."""

    def __init__(self):
        """Initialize the registry."""
        self._services = {}

    def register(self, service_instance, service_id=None):
        """Register a new service instance."""
        if service_id is None:
            service_id = service_instance.id
        if service_id in self._services:
            raise RuntimeError(
                f"Service with service id '{service_id}' " "is already registered."
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


class NotificationRegistry:
    """Notifications registry."""

    def __init__(self):
        """Constructor."""
        self._handlers = {}

    def register(self, record_type, handler):
        """Register a handler for a change notification."""
        if self._handlers.get(record_type, None):
            self._handlers[record_type].append(handler)
        else:
            self._handlers[record_type] = [handler]

    def get(self, record_type):
        """Get the list of handlers for a record type.

        Returns an empty list if not found.
        """
        return self._handlers.get(record_type, [])
