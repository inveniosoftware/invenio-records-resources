"""Example service."""

from invenio_records_resources.records.resolver import UUIDResolver
from invenio_records_resources.services import RecordService, \
    RecordServiceConfig
from invenio_records_resources.services.records.params import SortParam

from .api import Record
from .permissions import PermissionPolicy
from .schema import RecordSchema
from .search import RecordsSearch


class ServiceConfig(RecordServiceConfig):
    """Mock service configuration."""

    permission_policy_cls = PermissionPolicy
    record_cls = Record
    schema = RecordSchema
    search_cls = RecordsSearch



class Service(RecordService):
    """Mock service."""

    default_config = ServiceConfig
