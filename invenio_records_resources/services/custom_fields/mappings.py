# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Custom fields mappings."""

from abc import abstractmethod


class Mapping:
    """Base class for mappings."""

    @abstractmethod
    def to_dict(self):
        """Return the mapping as a dictionary."""


class KeywordMapping(Mapping):
    """Keyword mapping."""

    def to_dict(self):
        """Return the mapping."""
        return {"type": "keyword"}


class TextMapping(Mapping):
    """Text mapping."""

    def __init__(self, use_as_filter=False):
        """Constructor."""
        self._use_as_filter = use_as_filter

    def to_dict(self):
        """Return the mapping."""
        _mapping = {"type": "text"}
        if self._use_as_filter:
            _mapping["fields"] = {"keyword": {"type": "keyword"}}
        return _mapping


class EDTFMapping(Mapping):
    """EDTF mapping."""

    def to_dict(self):
        """Return the mapping as a dictionary."""
        return {
            "type": "object",
            "properties": {
                "date": {"type": "keyword"},
                "date_range": {"type": "date_range"},
            },
        }


class ISODateMapping(Mapping):
    """ISO date mapping."""

    def to_dict(self):
        """Return the mapping as a dictionary."""
        return {"type": "date"}
