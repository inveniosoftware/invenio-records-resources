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

    def __init__(self, name):
        """Constructor."""
        self.name = name
        self.relation_cls = None
        super().__init__()

    @property
    @abstractmethod
    def mapping(self):
        """Return the mapping."""
        pass

    @property
    @abstractmethod
    def field(self):
        """Marshmallow schema for vocabulary custom fields."""
        pass

    @property
    def ui_field(self):
        """Marshmallow UI schema for vocabulary custom fields."""
        return self.schema()
