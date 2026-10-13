# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Files stored in a bucket other than the record's main one."""

from io import BytesIO

from invenio_db import db
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_records.systemfields import ModelField

from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.records.systemfields import FilesField
from invenio_records_resources.services import FileService
from tests.mock_module.api import FileRecord, Record
from tests.mock_module.config import FileServiceConfig


class MediaRecord(Record):
    """Record whose files live in a separate media bucket."""

    files = FilesField(
        store=False,
        file_cls=FileRecord,
        create=False,
        bucket_id_attr="media_bucket_id",
        bucket_attr="media_bucket",
    )
    bucket_id = ModelField()
    bucket = ModelField(dump=False)

    @property
    def media_bucket_id(self):
        return self["media_bucket_id"]

    @property
    def media_bucket(self):
        return db.session.get(Bucket, self.media_bucket_id)


class MediaFileServiceConfig(FileServiceConfig):
    service_id = "media-files"
    record_cls = MediaRecord


def test_staged_upload_uses_files_bucket(
    location, input_data, identity_simple, set_app_config_fn_scoped
):
    """Staged uploads go to the files bucket, not the record's main one."""
    set_app_config_fn_scoped({"RECORDS_RESOURCES_USE_STAGED_TRANSFER": True})
    service = FileService(MediaFileServiceConfig)
    current_service_registry.register(service)
    # Like a published record, whose main bucket is locked.
    main_bucket = Bucket.create(locked=True)
    media_bucket = Bucket.create()
    record = MediaRecord.create({"media_bucket_id": str(media_bucket.id)}, **input_data)
    record.bucket = main_bucket
    record.commit()
    db.session.commit()
    recid = record["id"]

    service.init_files(identity_simple, recid, [{"key": "media.txt"}])
    service.set_file_content(identity_simple, recid, "media.txt", BytesIO(b"abc"), 3)
    service.commit_file(identity_simple, recid, "media.txt")

    assert ObjectVersion.get(media_bucket, "media.txt").file.size == 3
    assert ObjectVersion.get(main_bucket, "media.txt") is None
