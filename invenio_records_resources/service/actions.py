# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Actions API."""


class Action:
    """Action interface."""

    def __init__(self, state):
        """Initialize action."""
        self.state = state

    def run(self):
        """Run action."""
        raise NotImplementedError()


class MacroAction(Action):
    """Macro action for running multiple actions."""

    #: List of actions to execute
    actions = []

    def iter_actions(self):
        """Iterate over actions."""
        for a in self.actions:
            yield a(self.state)

    def run(self):
        """Run each action defined."""
        for a in self.iter_actions():
            a.run()


class PublishAction(MacroAction):
    """Record publishing action."""

    actions = []
