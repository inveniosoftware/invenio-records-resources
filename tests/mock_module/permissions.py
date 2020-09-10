"""Example of a permission policy."""

from flask_principal import Permission


class PermissionPolicy(Permission):

    def __init__(self, action_name, **kwargs):
        self.needs = set()
        self.excludes = set()
