# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service results."""


class ServiceResult:
    """Base class for a service result."""


class ServiceItemResult(ServiceResult):
    """Base class for a service result for a single item."""


class ServiceListResult(ServiceResult):
    """Base class for a service result for a list of items."""
