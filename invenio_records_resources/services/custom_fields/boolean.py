# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from marshmallow.fields import Boolean

from .base import BaseListCF, ensure_no_field_cls
from .mappings import BooleanMapping


class BooleanCF(BaseListCF):
    """Boolean custom field."""

    @ensure_no_field_cls
    def __init__(self, name, **kwargs):
        """Constructor."""
        # do not allow overridability of field_cls
        super().__init__(name, field_cls=Boolean, **kwargs)

    @property
    def mapping(self):
        """Return the mapping."""
        return BooleanMapping().to_dict()
