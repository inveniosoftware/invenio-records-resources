"""Example service."""

from invenio_records_resources.records.resolver import UUIDResolver
from invenio_records_resources.services import RecordService, \
    RecordServiceConfig

from .api import Record
from .permissions import PermissionPolicy
from .schema import RecordSchema


class ServiceConfig(RecordServiceConfig):
    """Mock service configuration."""

    record_cls = Record
    resolver_cls = UUIDResolver
    permission_policy_cls = PermissionPolicy
    schema = RecordSchema


class Service(RecordService):
    """Mock service."""

    default_config = ServiceConfig
