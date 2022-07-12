# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from .base import BaseCF
from .schema import CustomFieldsSchema, CustomFieldsSchemaUI
from .text import KeywordCF, TextCF

__all__ = (
    "BaseCF",
    "CustomFieldsSchema",
    "CustomFieldsSchemaUI",
    "KeywordCF",
    "TextCF",
)
