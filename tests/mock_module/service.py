"""Example service."""

from invenio_records_resources.records.resolver import UUIDResolver
from invenio_records_resources.services import RecordService, \
    RecordServiceConfig
from invenio_search import RecordsSearchV2

from .api import Record
from .permissions import PermissionPolicy
from .schema import RecordSchema


class ServiceConfig(RecordServiceConfig):
    """Mock service configuration."""

    permission_policy_cls = PermissionPolicy
    record_cls = Record
    schema = RecordSchema
    search_cls = RecordsSearchV2


class Service(RecordService):
    """Mock service."""

    default_config = ServiceConfig
