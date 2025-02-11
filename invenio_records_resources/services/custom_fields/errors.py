# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from abc import abstractmethod

from invenio_i18n import gettext as _


class CustomFieldsException(Exception):
    """Base class for custom fields exceptions."""

    @property
    @abstractmethod
    def description(self):
        """Exception's description."""
        raise NotImplementedError()


class InvalidCustomFieldsNamespace(CustomFieldsException):
    """Invalid namespace for a custom field check exception."""

    def __init__(self, field_name, given_namespace):
        """Constructor."""
        self.field_name = field_name
        self.given_namespace = given_namespace

    @property
    def description(self):
        """Exception's description."""
        return _(
            "Namespace %(given_namespace)s is not valid for custom field %(field_name)s.",
            given_namespace=self.given_namespace,
            field_name=self.field_name,
        )


class CustomFieldsNotConfigured(CustomFieldsException):
    """Invalid namespace for a custom field check exception."""

    def __init__(self, field_names):
        """Constructor."""
        self.field_names = field_names

    @property
    def description(self):
        """Exception's description."""
        return _(
            "Custom fields %(field_names)s are not configured.",
            field_names=self.field_names,
        )


class CustomFieldsInvalidArgument(CustomFieldsException):
    """Invalid argument passed when initializing custom field class."""

    def __init__(self, arg_name):
        """Constructor."""
        self.arg_name = arg_name

    @property
    def description(self):
        """Exception's description."""
        return _(
            "Invalid argument %(arg_name)s passed when initializing custom field.",
            arg_name=self.arg_name,
        )
