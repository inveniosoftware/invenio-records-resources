# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-License-Identifier: MIT

"""Search parameter interpreter API."""


class ParamInterpreter:
    """Evaluate a url parameter."""

    def __init__(self, config):
        """Initialise the parameter interpreter."""
        self.config = config

    def apply(self, identity, search, params):
        """Apply the parameters."""
