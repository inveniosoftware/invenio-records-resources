"""Example service."""

from invenio_records_resources.records.resolver import UUIDResolver
from invenio_records_resources.services import RecordService, \
    RecordServiceConfig
from invenio_records_resources.services.data_schema import \
    MarshmallowDataSchema

from .api import Record
from .permissions import PermissionPolicy
from .schema import RecordSchemaV1


class ServiceConfig(RecordServiceConfig):
    record_cls = Record
    resolver_cls = UUIDResolver
    permission_policy_cls = PermissionPolicy
    data_schema = MarshmallowDataSchema(schema=RecordSchemaV1)


class Service(RecordService):
    default_config = ServiceConfig
