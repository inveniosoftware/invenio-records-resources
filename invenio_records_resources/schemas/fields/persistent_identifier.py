# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Persistent Identifier field."""

from marshmallow import missing

from .generated import GenFunction


# FIXME: Is this still needed?
def pid_from_context(_, context, **kwargs):
    """Get PID from marshmallow context."""
    pid = (context or {}).get("pid")
    return pid.pid_value if pid else missing


class PersistentIdentifier(GenFunction):
    """Field to handle PersistentIdentifiers in records.

    .. versionadded:: 1.2.0
    """

    def __init__(self, *args, **kwargs):
        """Initialize field."""
        super(PersistentIdentifier, self).__init__(
            serialize=pid_from_context,
            deserialize=pid_from_context,
            *args,
            **kwargs
        )
