# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from marshmallow.fields import Boolean

from .base import BaseListCF
from .mappings import BooleanMapping


class BooleanCF(BaseListCF):
    """Boolean custom field."""

    def __init__(self, name, **kwargs):
        """Constructor."""
        super().__init__(name, field_cls=Boolean, **kwargs)

    @property
    def mapping(self):
        """Return the mapping."""
        return BooleanMapping().to_dict()
