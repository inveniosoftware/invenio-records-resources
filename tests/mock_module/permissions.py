"""Example of a permission policy."""

from flask_principal import Permission


class PermissionPolicy(Permission):
    """Mock permission policy."""

    def __init__(self, action_name, **kwargs):
        """Constructor."""
        self.needs = set()
        self.excludes = set()
