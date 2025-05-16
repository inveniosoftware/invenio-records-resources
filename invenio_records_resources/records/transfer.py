# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2023 CERN.
# Copyright (C) 2020-2021 Northwestern University.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Transfer-related system fields."""

#
# Implementation Note:
#
# This module cannot be placed under `systemfields/files` because `systemfields/files`
# imports several classes from outside the `records` module (e.g., `FilesAttrConfig`
# and `PartialFileDumper`). In turn, those classes import `records.api`, creating a
# circular import.
#
# Furthermore, we need `TransferField` defined directly on `FileRecord`. We cannot
# delegate this to the user (as is done with `FilesField`) because if a target
# repository has not declared the `transfer` field on its own `FileRecord`, file
# uploads would fail. Therefore, `TransferField` must be defined here.
#
# TODO: A cleaner solution would be to refactor `systemfields/files` so that it does
# not introduce dependencies outside the `records` module.
#

from collections.abc import Mapping

from invenio_records.systemfields import SystemField

from ..proxies import current_transfer_registry


class TransferFieldData(Mapping):
    """TransferType field data."""

    def __init__(self, field):
        """Initialize the field."""
        self._field = field

    @property
    def transfer_type(self):
        """Get the transfer type."""
        # the get here is for backwards compatibility, if the file record was created
        # before the transfer was added to the file record
        return self._field.get("type", current_transfer_registry.default_transfer_type)

    @transfer_type.setter
    def transfer_type(self, value):
        """Set the transfer type."""
        self._field["type"] = value

    def get(self, key, default=None):
        """Get the value from the transfer metadata."""
        return self._field.get(key, default)

    def set(self, values):
        """Set values of transfer metadata, keeping the transfer type."""
        transfer_type = self.transfer_type
        self._field.clear()
        self._field.update(values)
        self.transfer_type = transfer_type

    def __iter__(self):
        """Iterate over the transfer metadata."""
        return iter(self._field)

    def __len__(self):
        """Length of the transfer metadata."""
        return len(self._field)

    def __getitem__(self, key):
        """Get a value from the transfer metadata."""
        return self._field[key]

    def __setitem__(self, key, value):
        """Set a value in the transfer metadata."""
        self._field[key] = value


class TransferField(SystemField):
    """TransferType field.

    Gets/sets the transfer type of the file record.
    """

    def __get__(self, record, owner=None):
        """Getting the attribute value."""
        if record is None:
            return self
        ret = self.get_dictkey(record)
        if ret is None:
            ret = {}
            self.set_dictkey(record, ret)

        return TransferFieldData(ret)

    def __set__(self, record, value):
        """Setting a new value."""
        self.set_dictkey(record, value)
