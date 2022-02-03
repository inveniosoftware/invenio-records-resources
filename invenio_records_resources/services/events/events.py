# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Events module."""

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar


@dataclass
class Event:
    """Base event."""

    created: datetime
    type: str
    action: str
    handling_key: str


@dataclass
class RecordEvent(Event):
    """Record related events."""

    recid: str
    type: ClassVar[str] = "RECORD"
    handling_key: ClassVar[str] = "RECORD"


@dataclass
class RecordCreatedEvent(RecordEvent):
    """Record related events."""

    action: ClassVar[str] = "PUBLISHED"
    handling_key: ClassVar[str] = f"{RecordEvent.type}.{action}"
