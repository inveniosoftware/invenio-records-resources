# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records service component base classes."""

from ...uow import ChangeNotificationOp
from .base import ServiceComponent


class RelationsComponent(ServiceComponent):
    """Relations service component."""

    def read(self, identity, record=None):
        """Read record handler."""
        record.relations.dereference()


class ChangeNotificationsComponent(ServiceComponent):
    """Back Relations service component."""

    def update(self, identity, data=None, record=None, uow=None, **kwargs):
        """Register a task for the update propagation."""
        # FIXME: until the run_components has been fixed the uow
        # is passed as a cmp attr instead of param.
        self.uow.register(
            ChangeNotificationOp(
                record_type=self.service.id,
                records=[record],
            )
        )
