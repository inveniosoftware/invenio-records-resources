# SPDX-FileCopyrightText: 2020-2024 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-License-Identifier: MIT

"""Service results."""


class ServiceResult:
    """Base class for a service result."""


class ServiceItemResult(ServiceResult):
    """Base class for a service result for a single item."""


class ServiceListResult(ServiceResult):
    """Base class for a service result for a list of items."""


class ServiceBulkItemResult(ServiceResult):
    """Base class for a service result for a single item performed on a bulk operation."""


class ServiceBulkListResult(ServiceResult):
    """Base class for a service result for a list of items performed on a bulk operation."""
