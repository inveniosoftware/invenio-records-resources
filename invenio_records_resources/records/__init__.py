# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Data access layer."""

from .api import File, FileRecord, Record
from .models import FileRecordModelMixin

__all__ = (
    "File",
    "FileRecord",
    "FileRecordModelMixin",
    "Record",
)
