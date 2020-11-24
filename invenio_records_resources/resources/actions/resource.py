# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""


from flask import abort, g
from flask_resources import SingletonResource
from flask_resources.context import resource_requestctx

from ...config import ConfigLoaderMixin
from .config import ActionResourceConfig
from .errors import ActionNotImplementedError


class ActionResource(SingletonResource, ConfigLoaderMixin):
    """Action resource interface."""

    default_config = ActionResourceConfig

    def __init__(self, config=None, service=None):
        """Constructor."""
        super().__init__(config=self.load_config(config))
        self.service = service  # No service on this abstract level

    def _get_cmd_func(self, action, operation):
        """Get a function based on the operation name and the action."""
        try:
            op_cmds = self.config.action_commands[operation]
            cmd_name = op_cmds[action]
            cmd_func = getattr(self.service, cmd_name)
            return cmd_func
        except KeyError:  # Can be both operation or action
            raise abort(404)
        except AttributeError:
            raise ActionNotImplementedError(cmd_name)

    def handle_action_request(self, operation):
        """Execute an action based on an operation and the resource config."""
        action = resource_requestctx.route["action"]
        resource_func = getattr(self, f'{operation}_{action}', None)
        if not resource_func:
            abort(404)
        return resource_func(action, operation)

    # SingletonView POST
    def create(self, *args, **kwargs):
        """POST operations on actions."""
        return self.handle_action_request('create')

    # SingletonView PUT
    def update(self, *args, **kwargs):
        """PUT operations on actions."""
        return self.handle_action_request('update')

    # SingletonView GET
    def read(self, *args, **kwargs):
        """GET operations on actions."""
        return self.handle_action_request('read')

    # SingletonView DELETE
    def delete(self, *args, **kwargs):
        """DELETE operations on actions."""
        return self.handle_action_request('delete')
