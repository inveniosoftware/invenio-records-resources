# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from .schema import CustomFieldsSchema
from .service import CustomFieldsService, CustomFieldsServiceConfig
from .text import KeywordCF, TextCF
from .vocabulary import VocabularyCF

# TODO: Should this be a higher level package?
# and have fields and service separated?

__all__ = (
    "CustomFieldsSchema",
    "CustomFieldsService",
    "CustomFieldsServiceConfig"
    "KeywordCF",
    "TextCF",
    "VocabularyCF",
)
