# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Entity grants for permission/identity needs.

Entity grants are used to serialize permission needs into a record, so that
the records index can be efficiently filter to only records that a given user
have access to.

Following are examples for entity grant tokens:

- ``creator.user.1`` - expresses that the creator.user.1 is granted access.
- ``receiver.community.123.manager`` - expresses that the community 123
  managers are granted access.

Entity grants are created from needs, which means that you can generate the
grants from:

- required needs: e.g. a record requiring needs to grant access.
- provided needs: e.g. an identity providing needs.

This provides an for efficient searches when you serialize the required grants
into the indexed record, and when searching, you filter records to the grants
provided by the identity.
"""


class EntityGrant:
    """Represents a grant token value object."""

    def __init__(self, prefix, need):
        """Initialize entity grant."""
        self._prefix = prefix
        self._need = need

    @property
    def token(self):
        """Create the grant token."""
        # A need is just a tuple
        parts = (self._prefix,) + self._need
        return ".".join((str(p) for p in parts))

    def __str__(self):
        """String representation."""
        return self.token

    def __repr__(self):
        """Represent object as a string."""
        return f"<{self.__class__.__name__} '{self.token}'>"
