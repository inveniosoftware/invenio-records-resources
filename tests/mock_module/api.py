# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020-2023 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Example of a record API."""

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
from invenio_records.dumpers import SearchDumper
from invenio_records.dumpers.indexedat import IndexedAtDumperExt
from invenio_records.dumpers.relations import RelationDumperExt
from invenio_records.systemfields import ConstantField, ModelField, RelationsField

from invenio_records_resources.records.api import FileRecord as FileRecordBase
from invenio_records_resources.records.api import Record as RecordBase
from invenio_records_resources.records.systemfields import (
    FilesField,
    IndexField,
    PIDField,
    PIDRelation,
    PIDStatusCheckField,
)

from . import models


class FileRecord(FileRecordBase):
    """Example record file API."""

    model_cls = models.FileRecordMetadata
    record_cls = None  # is defined below


class DeletionStatus:
    """Mock of Deletion status field."""

    is_deleted = False


class Tombstone:
    """Mock of Tombstone system field."""

    is_visible = True
    citation_text = "citation text"
    removal_date = "2023-09-20T08:19:58.431539"
    removed_by = {"user": "system"}
    note = "spam"

    def dump(self):
        """Dump the values."""
        data = {
            "note": self.note,
            "removed_by": self.removed_by,
            "removal_date": self.removal_date,
            "citation_text": self.citation_text,
            "is_visible": self.is_visible,
        }

        return data


class Record(RecordBase):
    """Example record API."""

    # Configuration
    model_cls = models.RecordMetadata

    # Model fields
    expires_at = ModelField()

    # System fields
    schema = ConstantField("$schema", "local://records/record-v1.0.0.json")

    index = IndexField("records-record-v1.0.0", search_alias="records")

    pid = PIDField("id", provider=RecordIdProviderV2)

    conceptpid = PIDField("conceptid", provider=RecordIdProviderV2)

    is_published = PIDStatusCheckField(status=PIDStatus.REGISTERED)

    dumper = SearchDumper(
        extensions=[
            IndexedAtDumperExt(),
        ]
    )

    deletion_status = DeletionStatus()

    tombstone = Tombstone()


class RecordWithRelations(Record):
    """Example record API with relations."""

    relations = RelationsField(
        languages=PIDRelation(
            "metadata.inner_record", keys=["metadata.title"], pid_field=Record.pid
        )
    )

    dumper = SearchDumper(
        extensions=[
            RelationDumperExt("relations"),
            IndexedAtDumperExt(),
        ]
    )


class RecordWithFiles(Record):
    """Example record with file API."""

    files = FilesField(store=False, file_cls=FileRecord)
    bucket_id = ModelField()
    bucket = ModelField(dump=False)
    is_draft = False


FileRecord.record_cls = RecordWithFiles
