# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Errors."""

from abc import ABC, abstractmethod
from typing import List

from flask_babelex import gettext as _
from invenio_notifications.models import BroadcastNotification


class PayloadGenerator(ABC):
    """Payload generator for a notification."""

    @abstractmethod
    def run(self, **kwargs):
        """Generate payload."""
        return {}


class RecipientGenerator(ABC):
    """Recipient generator for a notification."""

    @abstractmethod
    def run(self, payload, **kwargs):
        """Generate recipients."""
        return []


class RecipientFilter(ABC):
    """Recipient filter for a notification."""

    @abstractmethod
    def run(self, recipients, **kwargs):
        """Filter recipients."""
        return []


class RecipientBackendTransform(ABC):
    """Recipient backend transform for a notification."""

    @abstractmethod
    def run(self, recipients, **kwargs):
        """Transform recipient backends."""
        return []


class NotificationBuilder:
    """Base notification builder."""

    payload_generator: List[PayloadGenerator]
    recipients_generator: List[RecipientGenerator]
    recipients_filters: List[PayloadGenerator]
    recipient_backend_transform: List[PayloadGenerator]

    type = "Notification"
    trigger = {}

    def __init__(self, trigger):
        """Initialize builder."""
        self.trigger = trigger

    def build(self, **kwargs):
        """Build notification based on specified generators, filters and transformers."""
        n = BroadcastNotification()
        n.type = self.type
        n.trigger = self.trigger

        for pg in self.payload_generator:
            n.data.update(pg.run(**kwargs))

        recipients = []
        for rg in self.recipients_generator:
            recipients.extend(rg.run(n.data, **kwargs))

        # NOTE: shall filters only operate on the users and their preferences?
        for rf in self.recipients_filters:
            recipients = rf.run(recipients, **kwargs)

        for rbt in self.recipient_backend_transform:
            recipients = rbt.run(recipients, **kwargs)

        # TODO: remove duplicate recipients/users by default or leave it up to the specific Notification?
        # TODO: remove recipients users without backends by default or leave it up to the specific Notification?
        #       A backend transform might remove certain backends from a recipient leading to no backends.
        n.recipients = recipients
        return n
