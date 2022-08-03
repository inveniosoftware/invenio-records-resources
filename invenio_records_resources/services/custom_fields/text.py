# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from marshmallow_utils.fields import SanitizedUnicode

from .base import BaseCF


class KeywordCF(BaseCF):
    """Keyword custom field."""

    def __init__(self, name, **kwargs):
        """Constructor."""
        super().__init__(name, **kwargs)

    @property
    def mapping(self):
        """Return the mapping."""
        return {"type": "keyword"}

    @property
    def field(self):
        """Marshmallow field custom fields."""
        return SanitizedUnicode(**self._field_args)


class TextCF(KeywordCF):
    """Text custom field."""

    def __init__(self, name, use_as_filter=False, **kwargs):
        """Constructor."""
        self.use_as_filter = use_as_filter
        super().__init__(name, **kwargs)

    @property
    def mapping(self):
        """Return the mapping."""
        _mapping = {"type": "text"}
        if self.use_as_filter:
            _mapping["fields"] = {"keyword": {"type": "keyword"}}
        return _mapping
