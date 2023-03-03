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
        raise NotImplementedError()

    @classmethod
    def properties_for_fields(cls, given_fields_name, available_fields):
        """Prepare search mapping properties for each field."""
        fields = []
        if given_fields_name:  # create only specified fields
            given_fields_name = set(given_fields_name)
            for a_field in available_fields:
                if a_field.name in given_fields_name:
                    fields.append(a_field)
                    given_fields_name.remove(a_field.name)
                if len(given_fields_name) == 0:
                    break
        else:  # create all fields
            fields = available_fields

        properties = {}
        for field in fields:
            properties[f"custom_fields.{field.name}"] = field.mapping

        return properties

    @classmethod
    def field_exists(cls, field_name, index):
        """Check if a field is present in `index`'s mapping."""
        mapping = list(index.get_mapping().values())[0]["mappings"]

        parts = field_name.split(".")
        for part in parts:
            mapping = mapping["properties"]  # here to avoid last field access
            if part not in mapping.keys():
                return False
            mapping = mapping[part]

        return True


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


class BooleanMapping(Mapping):
    """Boolean mapping."""

    def to_dict(self):
        """Return the mapping as a dictionary."""
        return {"type": "boolean"}


class IntegerMapping(Mapping):
    """Integer mapping."""

    def to_dict(self):
        """Return the mapping as a dictionary."""
        return {"type": "integer"}


class DoubleMapping(Mapping):
    """Double mapping."""

    def to_dict(self):
        """Return the mapping as a dictionary."""
        return {"type": "double"}
