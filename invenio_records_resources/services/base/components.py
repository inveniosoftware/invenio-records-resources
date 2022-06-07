# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Base class for all service components."""


class BaseServiceComponent:
    """Base service component."""

    def __init__(self, service, *args, **kwargs):
        """Initialize the base service component."""
        self.service = service
        self._uow = None

    @property
    def uow(self):
        """Get the Unit of Work manager."""
        if self._uow is None:
            # Warn about wrong usage
            raise RuntimeError("Method is not running in a unit of work context.")
        return self._uow

    @uow.setter
    def uow(self, value):
        """Set the Unit of Work manager."""
        if value is not None and self._uow is not None:
            # Don't set it twice.
            raise RuntimeError("Unit of work already set on component.")
        self._uow = value
