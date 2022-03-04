# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module for event driven actions support."""

from .bus import EventBus
from .events import Event

__all__ = (
    "Event",
    "EventBus"
)
