"""Example service."""

from invenio_records_resources.records.resolver import UUIDResolver
from invenio_records_resources.services import RecordService, \
    RecordServiceConfig

from .api import Record
from .permissions import PermissionPolicy


class ServiceConfig(RecordServiceConfig):
    record_cls = Record
    resolver_cls = UUIDResolver
    permission_policy_cls = PermissionPolicy


class Service(RecordService):
    default_config = ServiceConfig

