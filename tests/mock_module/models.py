# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Example of a record model."""

from invenio_db import db
from invenio_files_rest.models import Bucket
from invenio_pidstore.models import PIDStatus
from invenio_records.models import RecordMetadataBase
from sqlalchemy_utils.types import ChoiceType, UUIDType

from invenio_records_resources.records.models import FileRecordModelMixin


class RecordMetadata(db.Model, RecordMetadataBase):
    """Model for mock module metadata."""

    __tablename__ = "mock_metadata"

    expires_at = db.Column(db.DateTime(), nullable=True)

    bucket_id = db.Column(UUIDType, db.ForeignKey(Bucket.id))
    bucket = db.relationship(Bucket)


class RecordMetadataWithPID(db.Model, RecordMetadataBase):
    """Mock record metadata class."""

    __tablename__ = "mock_metadata_pid"

    pid = db.Column(db.String(255), unique=True)
    pid_status = db.Column(ChoiceType(PIDStatus, impl=db.CHAR(1)))


class FileRecordMetadata(db.Model, RecordMetadataBase, FileRecordModelMixin):
    """Model for mock module record files."""

    __record_model_cls__ = RecordMetadata

    __tablename__ = "mock_record_files"
