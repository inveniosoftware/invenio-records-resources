# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-License-Identifier: MIT

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
