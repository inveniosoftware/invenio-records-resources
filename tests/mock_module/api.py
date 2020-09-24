"""Example of a record API."""

from datetime import datetime

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
from invenio_records.systemfields import ConstantField, DictField, ModelField

from invenio_records_resources.records.api import Record as RecordBase
from invenio_records_resources.records.systemfields import IndexField, \
    PIDField, PIDStatusCheckField

from .models import RecordMetadata


class Record(RecordBase):
    """Example record API."""

    # Configuration
    model_cls = RecordMetadata

    # Model fields
    expires_at = ModelField()

    # System fields
    schema = ConstantField(
        '$schema', 'http://localhost/schemas/records/record-v1.0.0.json')

    index = IndexField('records-record-v1.0.0', search_alias='records')

    pid = PIDField('id', provider=RecordIdProviderV2)

    conceptpid = PIDField('conceptid', provider=RecordIdProviderV2)

    is_published = PIDStatusCheckField(status=PIDStatus.REGISTERED)
