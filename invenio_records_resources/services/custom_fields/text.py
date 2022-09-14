# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from marshmallow_utils.fields import SanitizedUnicode

from .base import BaseListCF
from .mappings import KeywordMapping, TextMapping


class KeywordCF(BaseListCF):
    """Keyword custom field."""

    def __init__(self, name, **kwargs):
        """Constructor."""
        super().__init__(name, field_cls=SanitizedUnicode, **kwargs)

    @property
    def mapping(self):
        """Return the mapping."""
        return KeywordMapping().to_dict()


class TextCF(KeywordCF):
    """Text custom field."""

    def __init__(self, name, use_as_filter=False, **kwargs):
        """Constructor."""
        super().__init__(name, **kwargs)
        self._use_as_filter = use_as_filter

    @property
    def mapping(self):
        """Return the mapping."""
        return TextMapping(use_as_filter=self._use_as_filter).to_dict()
