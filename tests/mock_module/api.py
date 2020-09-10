"""Example of a record API."""

from datetime import datetime

from invenio_records.systemfields import ConstantField, DictField, ModelField

from invenio_records_resources.records.api import Record as RecordBase

from .models import RecordMetadata


class Record(RecordBase):
    """Example record API."""

    # Record configuration
    model_cls = RecordMetadata

    # System fields
    schema = ConstantField(
        '$schema', 'http://localhost/schemas/records/record-v1.0.0.json')

    expires_at = ModelField()
