# SPDX-FileCopyrightText: 2020-2024 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-License-Identifier: MIT

"""Base Service API."""

from .config import ServiceConfig
from .links import (
    ConditionalLink,
    EndpointLink,
    ExternalLink,
    Link,
    LinksTemplate,
    NestedLinks,
)
from .results import ServiceItemResult, ServiceListResult
from .service import Service

__all__ = (
    "ConditionalLink",
    "EndpointLink",
    "ExternalLink",
    "Link",
    "LinksTemplate",
    "Service",
    "ServiceConfig",
    "ServiceItemResult",
    "ServiceListResult",
    "NestedLinks",
)
