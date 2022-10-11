# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Example of a permission policy."""

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, SystemProcess

from invenio_records_resources.services.files.generators import AnyUserIfFileIsLocal


class PermissionPolicy(RecordPermissionPolicy):
    """Mock permission policy. All actions allowed."""

    can_search = [AnyUser(), SystemProcess()]
    can_create = [AnyUser(), SystemProcess()]
    can_read = [AnyUser(), SystemProcess()]
    can_update = [AnyUser(), SystemProcess()]
    can_delete = [AnyUser(), SystemProcess()]
    can_create_files = [AnyUser(), SystemProcess()]
    can_set_content_files = [AnyUserIfFileIsLocal(), SystemProcess()]
    can_get_content_files = [AnyUserIfFileIsLocal(), SystemProcess()]
    can_commit_files = [AnyUserIfFileIsLocal(), SystemProcess()]
    can_read_files = [AnyUser(), SystemProcess()]
    can_update_files = [AnyUser(), SystemProcess()]
    can_delete_files = [AnyUser(), SystemProcess()]
