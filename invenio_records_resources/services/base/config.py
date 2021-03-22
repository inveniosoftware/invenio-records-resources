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

from .results import ServiceItemResult, ServiceListResult


class ServiceConfig:
    """Service Configuration."""

    # Common configuration for all Services
    permission_policy_cls = BasePermissionPolicy
    result_item_cls = ServiceItemResult
    result_list_cls = ServiceListResult
