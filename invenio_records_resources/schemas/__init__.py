# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Marshmallow utilities."""

from .permissions import FieldPermissionError, FieldPermissionsMixin

__all__ = (
    'FieldPermissionError',
    'FieldPermissionsMixin',
)
