# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from marshmallow.fields import Float, Integer

from .base import BaseListCF
from .mappings import DoubleMapping, IntegerMapping


class IntegerCF(BaseListCF):
    """Integer custom field."""

    def __init__(self, name, **kwargs):
        """Constructor."""
        # strict=True to only allow int values
        super().__init__(name, field_cls=Integer, **kwargs)
        self._field_args["strict"] = True

    @property
    def mapping(self):
        """Return the mapping."""
        return IntegerMapping().to_dict()


class DoubleCF(BaseListCF):
    """Double custom field."""

    def __init__(self, name, **kwargs):
        """Constructor."""
        # Marshmallow floats are IEEE-754 doubles
        super().__init__(name, field_cls=Float, **kwargs)

    @property
    def mapping(self):
        """Return the mapping."""
        return DoubleMapping().to_dict()
