# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 - 2022 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Systemfield for calculated properties of records."""


import abc

from invenio_records.systemfields import SystemField


class CalculatedField(SystemField, abc.ABC):
    """Systemfield for returning calculated properties."""

    def __init__(self, key=None, use_cache=False):
        """Constructor."""
        super().__init__(key)
        self._use_cache = use_cache

    def obj(self, instance):
        """Calculate and return the record's property."""
        # per default, no caching should be used
        if not self._use_cache:
            return self.calculate(instance)

        # check the cache
        obj = self._get_cache(instance)
        if obj is not None:
            return obj

        # calculate and set cache
        obj = self.calculate(instance)
        self._set_cache(instance, obj)
        return obj

    def __get__(self, record, owner=None):
        """Calculate and return the record's property."""
        if record is None:
            # access by class
            return self

        return self.obj(record)

    def __set__(self, record, value):
        """Prevent setting of a calculated property."""
        msg = f"Cannot set value for calculated field '{self.key}'"
        raise AttributeError(msg)

    @abc.abstractmethod
    def calculate(self, record):
        """Logic for calculating the record's property."""
        return None


class CalculatedIndexedField(CalculatedField):
    """Field that also indexes its calculated value."""

    def __init__(self, key=None, use_cache=False, index=False):
        """Constructor."""
        super().__init__(key, use_cache=use_cache)
        self._index = index

    def pre_dump(self, record, data, dumper=None):
        """Called after a record is dumped."""
        if self._index:
            data[self.attr_name] = self.obj(record)

    def post_load(self, record, data, loader=None):
        """Called after a record is loaded."""
        if self._index:
            value = data.pop(self.attr_name, None)
            # Store on cache so if cache is used we don't fetch the object again.
            self._set_cache(record, value)
