"""Example of a record model."""

from invenio_db import db
from invenio_records.models import RecordMetadataBase


class RecordMetadata(db.Model, RecordMetadataBase):
    """Model for mock module metadata."""

    __tablename__ = 'mock_metadata'

    expires_at = db.Column(
        db.DateTime(),
        nullable=True
    )
