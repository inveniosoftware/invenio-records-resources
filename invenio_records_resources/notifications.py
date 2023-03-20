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
from datetime import datetime
from typing import List

from invenio_notifications.models import BroadcastNotification, BroadcastRecipient


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


# NOTE: Move to base backend implementation? It should probably dictate which
#       information it needs to generate the payload and it knows its id.
class BackendPayloadGenerator(ABC):
    """Backend generator for a notification."""

    backend_id: str
    template: str

    @abstractmethod
    def run(self, user, **kwargs):
        """Generate backend payload.

        The returned data should at least consist of:
            "id": stating the backend id
            "template": template name
        """
        return {
            "id": self.backend_id,
            "template": self.template,
        }


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

    payload_generators: List[PayloadGenerator] = []
    recipients_generators: List[RecipientGenerator] = []
    recipients_filters: List[PayloadGenerator] = []
    backend_payload_generators: List[BackendPayloadGenerator] = []
    recipient_backend_transforms: List[PayloadGenerator] = []

    type = "Notification"
    trigger = {}

    def __init__(self, trigger):
        """Initialize builder."""
        self.trigger = trigger

    def build(self, **kwargs):
        """Build notification based on specified generators, filters and transformers."""
        data = {}
        for pg in self.payload_generators:
            data.update(pg.run(**kwargs))

        users = []
        # NOTE: should only kwargs be passed?
        for rg in self.recipients_generators:
            users.extend(rg.run(data, **kwargs))

        recipients = []
        for u in users:
            backends = [bpg.run(u, **kwargs) for bpg in self.backend_payload_generators]
            recipients.append(
                BroadcastRecipient(
                    user=u,
                    backends=backends,
                )
            )

        # NOTE: shall filters only operate on the users and their preferences?
        for rf in self.recipients_filters:
            recipients = rf.run(recipients, **kwargs)

        for rbt in self.recipient_backend_transforms:
            recipients = rbt.run(recipients, **kwargs)

        # TODO: remove duplicate recipients/users by default or leave it up to the specific Notification?
        # TODO: remove recipients users without backends by default or leave it up to the specific Notification?
        #       A backend transform might remove certain backends from a recipient leading to no backends.

        return BroadcastNotification(
            type=self.type,
            trigger=self.trigger,
            data=data,
            recipients=recipients,
            timestamp=datetime.now().isoformat(),
        )
