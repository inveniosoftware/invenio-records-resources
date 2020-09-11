# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File service results."""

from ..base import ServiceItemResult, ServiceListResult


class InvenioFile(ServiceItemResult):
    """Fake File resource unit."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        pass


class FileMetadata(ServiceItemResult):
    """TODO: Replace this fake File metadata resource unit."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        pass


class FilesMetadata(ServiceListResult):
    """TODO: Replace this fake File metadata resource list."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        pass
