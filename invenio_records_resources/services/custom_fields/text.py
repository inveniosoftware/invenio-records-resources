# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from marshmallow import fields
from marshmallow_utils.fields import SanitizedUnicode

from .base import BaseListCF


class KeywordCF(BaseListCF):
    """Keyword custom field."""

    @property
    def mapping(self):
        """Return the mapping."""
        return {"type": "keyword"}

    @property
    def field(self):
        """Marshmallow field custom fields."""
        _schema = SanitizedUnicode(**self._field_args)
        if self._multiple:
            return fields.List(_schema)
        return _schema


class TextCF(KeywordCF):
    """Text custom field."""

    def __init__(self, name, use_as_filter=False, **kwargs):
        """Constructor."""
        super().__init__(name, **kwargs)
        self._use_as_filter = use_as_filter

    @property
    def mapping(self):
        """Return the mapping."""
        _mapping = {"type": "text"}
        if self._use_as_filter:
            _mapping["fields"] = {"keyword": {"type": "keyword"}}
        return _mapping
