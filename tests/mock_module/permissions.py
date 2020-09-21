"""Example of a permission policy."""

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser


class PermissionPolicy(RecordPermissionPolicy):
    """Mock permission policy. All actions allowed."""

    can_search = [AnyUser()]
    can_create = [AnyUser()]
    can_read = [AnyUser()]
    can_update = [AnyUser()]
    can_delete = [AnyUser()]
    can_read_files = [AnyUser()]
    can_update_files = [AnyUser()]
