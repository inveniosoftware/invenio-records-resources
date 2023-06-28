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

from ...base.components import BaseServiceComponent


class ServiceComponent(BaseServiceComponent):
    """Base service component."""

    def create(self, identity, **kwargs):
        """Create handler."""
        pass

    def read(self, identity, **kwargs):
        """Read handler."""
        pass

    def update(self, identity, **kwargs):
        """Update handler."""
        pass

    def delete(self, identity, **kwargs):
        """Delete handler."""
        pass

    def search(self, identity, search, params, **kwargs):
        """Search handler."""
        return search
