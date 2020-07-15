# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""A special system identity that allows all operations."""

from flask_principal import Identity


class SystemIdentity(Identity):
    """System identity - everything is allowed."""

    def __init__(self):
        """Initialize the system identity."""
        super(SystemIdentity, self).__init__(self, None)

    @property
    def provides(self):
        """Needs provided by this identity."""
        # TODO: fake it so permission.allows(system_identity) always works
        # Integrating with invenio-records-permissions
        return set()
