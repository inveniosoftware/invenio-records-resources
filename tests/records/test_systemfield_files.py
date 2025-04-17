# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files field tests."""

from io import BytesIO

from invenio_files_rest.models import Bucket, FileInstance, ObjectVersion
from invenio_records.systemfields import ConstantField, ModelField

from invenio_records_resources.records.dumpers import PartialFileDumper
from invenio_records_resources.records.systemfields.files import FilesField
from tests.mock_module import models
from tests.mock_module.api import FileRecord
from tests.mock_module.api import Record as RecordBase


# Define a files-enabled record class
class Record(RecordBase):
    files = FilesField(store=True, file_cls=FileRecord)
    bucket_id = ModelField()
    bucket = ModelField(dump=False)


class Record2(RecordBase):
    schema = ConstantField("$schema", "local://records/record-nofiles-v1.0.0.json")
    files = FilesField(store=False, dump=True, file_cls=FileRecord)
    bucket_id = ModelField()
    bucket = ModelField(dump=False)


def test_class_attribute_access():
    """Test that field is returned."""
    assert isinstance(Record.files, FilesField)


def test_record_files_creation(base_app, db, location):
    """Test record files bucket creation."""
    record = Record.create({})
    assert record.bucket_id
    assert record.bucket
    assert record.files.enabled is True
    assert record.files.default_preview is None
    assert record.files.order == []
    assert len(record.files) == 0
    assert set(record.files) == set()

    assert record["files"]
    assert record["files"]["enabled"] is True
    assert "default_preview" not in record["files"]
    assert "order" not in record["files"]
    assert record["files"]["entries"] == {}


def test_record_files_deletion(base_app, db, location):
    """Test record files bucket deletion."""
    record = Record.create({})
    bucket_id = record.bucket_id
    db.session.commit()
    assert Bucket.query.count() == 1
    assert Bucket.query.get(bucket_id)

    record.delete()
    db.session.commit()
    assert Bucket.query.count() == 1  # we soft-delete the bucket


def test_record_files_operations(base_app, db, location):
    """Test record files bucket creation."""
    record = Record.create({})

    # Initialize a file
    record.files["test.pdf"] = {"metadata": {"description": "A test file."}}
    rf = record.files["test.pdf"]
    assert rf.key == "test.pdf"
    assert rf.object_version is None
    assert rf.object_version_id is None
    assert rf.record_id is not None
    assert rf.record_id == record.id
    assert rf.metadata == {"description": "A test file."}
    assert rf["metadata"] == {"description": "A test file."}
    db.session.commit()

    assert models.FileRecordMetadata.query.count() == 1
    assert ObjectVersion.query.count() == 0

    # Update the file's metadata
    record.files["test.pdf"] = {"metadata": {"description": "A new description"}}
    rf = record.files["test.pdf"]
    assert rf.key == "test.pdf"
    assert rf.object_version is None
    assert rf.object_version_id is None
    assert rf.record_id is not None
    assert rf.record_id == record.id
    assert rf.metadata == {"description": "A new description"}
    assert rf["metadata"] == {"description": "A new description"}

    # Add an actual file
    dummy_file = BytesIO(b"testfile")
    record.files["test.pdf"] = dummy_file
    rf = record.files["test.pdf"]
    assert rf.key == "test.pdf"
    assert rf.object_version
    assert rf.object_version_id
    assert rf.object_version.key == rf.key == "test.pdf"
    assert rf.object_version.file
    assert rf.metadata == {"description": "A new description"}
    assert rf["metadata"] == {"description": "A new description"}
    db.session.commit()

    assert FileInstance.query.count() == 1
    assert ObjectVersion.query.count() == 1

    # Delete the file and the object version
    record.files.delete("test.pdf", softdelete_obj=False, remove_rf=True)
    record.commit()
    db.session.commit()

    assert models.FileRecordMetadata.query.count() == 0
    assert FileInstance.query.count() == 1
    assert ObjectVersion.query.count() == 0
    assert Bucket.query.count() == 1
    assert len(record.files) == 0
    assert "test.pdf" not in record.files
    assert record["files"]["entries"] == {}


def test_record_files_clear(base_app, db, location):
    """Test clearing record files (hard deletion)."""
    record = Record.create({})

    # Add a file with metadata + bytes
    record.files["f1.pdf"] = (
        BytesIO(b"testfile"),
        {"metadata": {"description": "Test file"}},
    )
    # Add a file with only bytes
    record.files["f2.pdf"] = BytesIO(b"testfile")
    # Add a file with only metadata
    record.files["f3.pdf"] = {"metadata": {"description": "Metadata only"}}
    record.commit()
    db.session.commit()

    assert models.FileRecordMetadata.query.count() == 3
    assert FileInstance.query.count() == 2
    assert ObjectVersion.query.count() == 2
    assert Bucket.query.count() == 1
    assert len(record.files) == 3

    # Delete all files
    record.files.delete_all(softdelete_obj=False, remove_rf=True)
    record.commit()
    db.session.commit()

    assert models.FileRecordMetadata.query.count() == 0
    assert FileInstance.query.count() == 2
    assert ObjectVersion.query.count() == 0
    assert Bucket.query.count() == 1
    assert len(record.files) == 0
    assert "f1.pdf" not in record.files
    assert "f2.pdf" not in record.files
    assert "f3.pdf" not in record.files
    assert record["files"]["entries"] == {}


def test_record_files_teardown_full(base_app, db, location):
    """Test clearing record files (hard deletion)."""
    record = Record.create({})

    # Add a file with metadata + bytes
    record.files["f1.pdf"] = (
        BytesIO(b"testfile"),
        {"metadata": {"description": "Test file"}},
    )
    # Add a file with only bytes
    record.files["f2.pdf"] = BytesIO(b"testfile")
    # Add a file with only metadata
    record.files["f3.pdf"] = {"metadata": {"description": "Metadata only"}}
    record.commit()
    db.session.commit()

    assert models.FileRecordMetadata.query.count() == 3
    assert FileInstance.query.count() == 2
    assert ObjectVersion.query.count() == 2
    assert Bucket.query.count() == 1
    assert len(record.files) == 3

    # Delete all files
    record.files.teardown(full=True)
    record.commit()
    db.session.commit()

    assert models.FileRecordMetadata.query.count() == 0
    assert FileInstance.query.count() == 2
    assert ObjectVersion.query.count() == 0
    assert Bucket.query.count() == 0
    assert len(record.files) == 0
    assert "f1.pdf" not in record.files
    assert "f2.pdf" not in record.files
    assert "f3.pdf" not in record.files
    assert record["files"]["entries"] == {}


def test_record_files_teardown_partial(base_app, db, location):
    """Test soft deleting record files."""
    record = Record.create({})

    # Add a file with metadata + bytes
    record.files["f1.pdf"] = (
        BytesIO(b"testfile"),
        {"metadata": {"description": "Test file"}},
    )
    # Add a file with only bytes
    record.files["f2.pdf"] = BytesIO(b"testfile")
    # Add a file with only metadata
    record.files["f3.pdf"] = {"metadata": {"description": "Metadata only"}}
    record.commit()
    db.session.commit()

    assert models.FileRecordMetadata.query.count() == 3
    assert FileInstance.query.count() == 2
    assert ObjectVersion.query.count() == 2
    assert Bucket.query.count() == 1
    assert len(record.files) == 3

    # Delete all files
    record.files.teardown(full=False)
    record.commit()
    db.session.commit()

    object_versions = ObjectVersion.query.filter_by(is_head=True).all()
    assert len(object_versions) == 2
    assert object_versions[0].deleted is False
    assert object_versions[1].deleted is False

    assert models.FileRecordMetadata.query.count() == 0
    assert FileInstance.query.count() == 2
    assert ObjectVersion.query.count() == 2
    assert Bucket.query.count() == 1
    assert len(record.files) == 0
    assert "f1.pdf" not in record.files
    assert "f2.pdf" not in record.files
    assert "f3.pdf" not in record.files
    assert record["files"]["entries"] == {}


def test_record_files_soft_delete(base_app, db, location):
    """Test soft deleting record files."""
    record = Record.create({})

    # Add a file with metadata + bytes
    record.files["f1.pdf"] = (
        BytesIO(b"testfile"),
        {"metadata": {"description": "Test file"}},
    )
    # Add a file with only bytes
    record.files["f2.pdf"] = BytesIO(b"testfile")
    # Add a file with only metadata
    record.files["f3.pdf"] = {"metadata": {"description": "Metadata only"}}
    record.commit()
    db.session.commit()

    assert models.FileRecordMetadata.query.count() == 3
    assert FileInstance.query.count() == 2
    assert ObjectVersion.query.count() == 2
    assert Bucket.query.count() == 1
    assert len(record.files) == 3

    # Delete all files
    record.files.delete_all(softdelete_obj=True, remove_rf=True)
    record.commit()
    db.session.commit()

    object_versions = ObjectVersion.query.filter_by(is_head=True).all()
    assert len(object_versions) == 2
    assert object_versions[0].deleted is True
    assert object_versions[1].deleted is True

    assert models.FileRecordMetadata.query.count() == 0
    assert FileInstance.query.count() == 2
    assert ObjectVersion.query.count() == 4
    assert Bucket.query.count() == 1
    assert len(record.files) == 0
    assert "f1.pdf" not in record.files
    assert "f2.pdf" not in record.files
    assert "f3.pdf" not in record.files
    assert record["files"]["entries"] == {}


def test_record_files_store(base_app, db, location):
    """Test JSON stored for files."""
    record = Record.create({})

    # Add a file with bytes + metadata
    record.files["f1.pdf"] = (
        BytesIO(b"testfile"),
        {"metadata": {"description": "Test file"}},
    )
    # Add a file with only bytes
    record.files["f2.pdf"] = BytesIO(b"testfile")

    rf1 = record.files["f1.pdf"]
    rf2 = record.files["f2.pdf"]
    record.commit()
    assert record["files"]["entries"] == {
        rf.key: {
            "checksum": rf.file.checksum,
            "ext": rf.file.ext,
            "file_id": str(rf.file.file_id),
            "key": rf.key,
            "metadata": rf.metadata or {},
            "mimetype": rf.file.mimetype,
            "object_version_id": str(rf.object_version_id),
            "size": rf.file.size,
            "uuid": str(rf.id),
            "version_id": rf.model.version_id,
        }
        for rf in (rf1, rf2)
    }


def test_record_files_copy(base_app, db, location):
    """Test record files bucket creation."""
    # Create source record
    src = Record.create({})
    src.files["f1.pdf"] = (
        BytesIO(b"testfile"),
        {"metadata": {"description": "Test file"}},
    )
    src.files.default_preview = "f1.pdf"
    src.files.order = ["f1.pdf"]
    src.commit()
    db.session.commit()

    assert ObjectVersion.query.count() == 1
    assert Bucket.query.count() == 1

    # Create destination record
    dst = Record.create({})
    dst.files.copy(src.files)
    dst.commit()
    db.session.commit()

    assert ObjectVersion.query.count() == 2
    assert Bucket.query.count() == 2

    assert dst.files.enabled == src.files.enabled
    assert dst.files.default_preview == src.files.default_preview
    assert dst.files.order == src.files.order
    assert list(dst.files.keys()) == list(src.files.keys())
    assert (
        dst.files["f1.pdf"].object_version.version_id
        != src.files["f1.pdf"].object_version.version_id
    )
    db.session.commit()

    # Unset preview and test sync()
    src.files.default_preview = None
    src.files.order = []
    db.session.commit()
    dst.files.sync(src.files)
    assert dst.files.default_preview is None
    assert dst.files.order == []


def test_record_files_copy_disabled(base_app, db, location):
    src = Record.create({})
    assert src.files.enabled is True
    src.files.enabled = False
    src.commit()
    db.session.commit()
    assert src.files.enabled is False

    # Create destination record
    dst = Record.create({})
    assert dst.files.enabled is True
    dst.files.copy(src.files)
    assert dst.files.enabled is False


def test_record_files_dump(base_app, db, location):
    """Test dumped data for record."""
    record = Record2.create({})
    record.files["f1.txt"] = (
        BytesIO(b"testfile"),
        {"metadata": {"description": "Test file"}},
    )
    rf = record.files["f1.txt"]
    record.commit()

    # Assert files data dumped inside the record
    data = record.dumps()
    assert data["files"] == {
        "enabled": True,
        "count": 1,
        "mimetypes": ["text/plain"],
        "totalbytes": 8,
        "types": ["txt"],
        "entries": [
            {
                "uuid": str(rf.id),
                "version_id": 3,
                "metadata": {"description": "Test file"},
                "checksum": "md5:8bc944dbd052ef51652e70a5104492e3",
                "key": "f1.txt",
                "mimetype": "text/plain",
                "size": 8,
                "ext": "txt",
                "object_version_id": str(rf.file.version_id),
                "file_id": str(rf.file.file_id),
            }
        ],
    }

    # Load data
    new_record = Record2.loads(data)
    new_rf = new_record.files["f1.txt"]
    assert new_rf.dumps(dumper=PartialFileDumper()) == rf.dumps(
        dumper=PartialFileDumper()
    )
    assert new_record == record


def test_record_files_access_explicit_set(base_app, db, location):
    """Test record files access, when explicitely set.

    When the access field is set, it should be dumped.
    """
    record = Record.create({})
    record.files["f1.txt"] = (
        BytesIO(b"testfile"),
        {"metadata": {"description": "Test file"}, "access": {"hidden": True}},
    )
    rf = record.files["f1.txt"]
    assert rf.access.hidden is True
    record.commit()
    data = record.dumps()
    assert data["files"]["entries"][0]["access"] == {"hidden": True}
    assert record.files["f1.txt"].model.json["access"] == {"hidden": True}


def test_record_files_access_implicit_not_set(base_app, db, location):
    """Test record files access, when not implicitely set.

    When the access field is not set, it should not be dumped.
    """
    record = Record.create({})
    record.files["f1.txt"] = BytesIO(b"testfile")
    rf = record.files["f1.txt"]
    assert rf.access.hidden is False
    record.commit()
    data = record.dumps()
    assert data["files"]["entries"][0].get("access") is None
    assert record.files["f1.txt"].model.json.get("access") is None
