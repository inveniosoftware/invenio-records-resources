# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service API."""

from invenio_records_permissions.policies import BasePermissionPolicy

# NOTE: needed to allow only one `.config` import in the service file
from ...config import ConfigLoaderMixin
from .results import ServiceItemResult, ServiceListResult


class ServiceConfig:
    """Service Configuration."""

    # Common configuration for all Services
    permission_policy_cls = BasePermissionPolicy
    """The permission policy class to use."""

    result_item_cls = ServiceItemResult
    result_list_cls = ServiceListResult
