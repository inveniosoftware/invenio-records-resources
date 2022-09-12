# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""


from abc import abstractmethod


class CustomFieldsException(Exception):
    """Base class for custom fields exceptions."""

    @property
    @abstractmethod
    def description(self):
        """Exception's description."""
        pass


class InvalidCustomFieldsNamespace(CustomFieldsException):
    """Invalid namespace for a custom field check exception."""

    def __init__(self, field_name, given_namespace):
        """Constructor."""
        self.field_name = field_name
        self.given_namespace = given_namespace

    @property
    def description(self):
        """Exception's description."""
        return (
            f"Namespace {self.given_namespace} is not valid for custom field "
            f"{self.field_name}."
        )


class CustomFieldsNotConfigured(CustomFieldsException):
    """Invalid namespace for a custom field check exception."""

    def __init__(self, field_names):
        """Constructor."""
        self.field_names = field_names

    @property
    def description(self):
        """Exception's description."""
        return f"Custom fields {self.field_names} are not configured."
