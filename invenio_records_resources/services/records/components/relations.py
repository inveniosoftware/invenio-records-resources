# SPDX-FileCopyrightText: 2020-2022 CERN.
# SPDX-FileCopyrightText: 2021 Northwestern University.
# SPDX-FileCopyrightText: 2023 Graz University of Technology.
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Records service component base classes."""

from ...uow import ChangeNotificationOp
from .base import ServiceComponent


class RelationsComponent(ServiceComponent):
    """Relations service component."""

    def read(self, identity, record=None, **kwargs):
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
