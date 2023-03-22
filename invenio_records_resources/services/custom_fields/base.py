# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from abc import ABC, abstractproperty
from functools import wraps

from marshmallow.fields import List

from .errors import CustomFieldsInvalidArgument


class BaseCF(ABC):
    """Base Custom Field class."""

    def __init__(self, name, field_args=None):
        """Constructor."""
        self.name = name
        self._field_args = field_args or {}
        super().__init__()

    @property
    @abstractproperty
    def mapping(self):
        """Return the mapping."""
        pass

    @property
    @abstractproperty
    def field(self):
        """Marshmallow field for custom fields."""
        pass

    @property
    def ui_field(self):
        """Marshmallow UI field for custom fields."""
        return self.field

    def dump(self, record, cf_key="custom_fields"):
        """Dump the custom field.

        Gets both the record and the custom fields key as parameters.
        This supports the case where a field is based on others, both
        custom and non-custom fields.
        """
        pass  # no change applied

    def load(self, record, cf_key="custom_fields"):
        """Load the custom field.

        Gets both the record and the custom fields key as parameters.
        This supports the case where a field is based on others, both
        custom and non-custom fields.
        """
        pass  # no change applied


class BaseListCF(BaseCF):
    """Base Custom Field class."""

    def __init__(self, name, field_cls, multiple=False, **kwargs):
        """Constructor.

        :param field_cls: The Marshmallow field class to use.
        :param multiple: If True, the field will be a List field.
        """
        super().__init__(name, **kwargs)
        self._multiple = multiple
        self._field_cls = field_cls

    @property
    def field(self):
        """Marshmallow field custom fields."""
        _field = self._field_cls(**self._field_args)

        return List(_field) if self._multiple else _field


def ensure_no_field_cls(func):
    """Decorator for ensuring that field_cls is not passed as kwarg.

    This is meant to be used in interfaces that implement the `BaseListCF` and they
    provide a concrete definition of the field cls.
    """

    @wraps(func)
    def inner(self, *args, **kwargs):
        if "field_cls" in kwargs:
            raise CustomFieldsInvalidArgument("field_cls")
        return func(self, *args, **kwargs)

    return inner
