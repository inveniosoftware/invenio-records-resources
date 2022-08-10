# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from abc import ABC, abstractmethod


class BaseCF(ABC):
    """Base Custom Field class."""

    def __init__(self, name, namespace=None, field_args=None):
        """Constructor."""
        self.name = name
        self.namespace = namespace or ""
        self._field_args = field_args or {}
        super().__init__()

    @property
    @abstractmethod
    def mapping(self):
        """Return the mapping."""
        pass

    @property
    @abstractmethod
    def field(self):
        """Marshmallow field for custom fields."""
        pass

    @property
    def ui_field(self):
        """Marshmallow UI field for custom fields."""
        return self.field

    @property
    def uri(self):
        """Field's uri.

        Return this field's urn in the format <namespace:name>.
        """
        return f"{self.namespace}:{self.name}" if self.namespace else self.name