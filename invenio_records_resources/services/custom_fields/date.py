# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from marshmallow import fields
from marshmallow_utils.fields import EDTFDateString, ISODateString

from .base import BaseListCF


class ISODateStringCF(BaseListCF):
    """ISO date custom field."""

    def __init__(self, name, **kwargs):
        """Constructor."""
        super().__init__(name, field_cls=ISODateString, **kwargs)

    @property
    def mapping(self):
        """Return the mapping."""
        return {"type": "date"}


class EDTFDateStringCF(BaseListCF):
    """EDTF date custom field."""

    def __init__(self, name, **kwargs):
        """Constructor."""
        super().__init__(name, field_cls=EDTFDateString, **kwargs)

    @property
    def mapping(self):
        """Return the mapping."""
        return {"type": "date", "fields": {"date_range": {"type": "date_range"}}}
