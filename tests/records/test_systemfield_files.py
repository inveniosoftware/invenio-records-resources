# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files field tests."""


from io import BytesIO

from invenio_files_rest.models import Bucket, FileInstance, Location, \
    ObjectVersion
from invenio_records.systemfields import ModelField
from mock_module import models
from mock_module.api import Record as RecordBase
from mock_module.api import RecordFile

from invenio_records_resources.records.systemfields.files import FilesField


# Define a files-enabled record class
class Record(RecordBase):

    files = FilesField(store=True, file_cls=RecordFile)
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

    assert record['files']
    assert record['files']['enabled'] is True
    assert 'default_preview' not in record['files']
    assert 'order' not in record['files']
    assert record['files']['entries'] == {}


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
    record.files['test.pdf'] = {'description': 'A test file.'}
    rf = record.files['test.pdf']
    assert rf.key == 'test.pdf'
    assert rf.object_version is None
    assert rf.object_version_id is None
    assert rf.record_id is not None
    assert rf.record_id == record.id
    assert rf.metadata == {'description': 'A test file.'}
    assert rf['metadata'] == {'description': 'A test file.'}
    db.session.commit()

    assert models.RecordFile.query.count() == 1
    assert ObjectVersion.query.count() == 0

    # Update the file's metadata
    record.files['test.pdf'] = {'description': 'A new description'}
    rf = record.files['test.pdf']
    assert rf.key == 'test.pdf'
    assert rf.object_version is None
    assert rf.object_version_id is None
    assert rf.record_id is not None
    assert rf.record_id == record.id
    assert rf.metadata == {'description': 'A new description'}
    assert rf['metadata'] == {'description': 'A new description'}

    # Add an actual file
    dummy_file = BytesIO(b'testfile')
    record.files['test.pdf'] = dummy_file
    rf = record.files['test.pdf']
    assert rf.key == 'test.pdf'
    assert rf.object_version
    assert rf.object_version_id
    assert rf.object_version.key == rf.key == 'test.pdf'
    assert rf.object_version.file
    assert rf.metadata == {'description': 'A new description'}
    assert rf['metadata'] == {'description': 'A new description'}
    db.session.commit()

    assert FileInstance.query.count() == 1
    assert ObjectVersion.query.count() == 1

    # Delete the file
    del record.files['test.pdf']
    record.commit()
    db.session.commit()

    assert models.RecordFile.query.count() == 0
    assert FileInstance.query.count() == 1
    assert ObjectVersion.query.count() == 2  # original + delete marker
    assert Bucket.query.count() == 1
    assert len(record.files) == 0
    assert 'test.pdf' not in record.files
    assert record['files']['entries'] == {}
    assert record['files']['meta'] == {}


def test_record_files_clear(base_app, db, location):
    """Test clearing record files."""
    record = Record.create({})

    # Add a file with metadata + bytes
    record.files['f1.pdf'] = (
        BytesIO(b'testfile'),
        {'description': 'Test file'}
    )
    # Add a file with only bytes
    record.files['f2.pdf'] = BytesIO(b'testfile')
    # Add a file with only metadata
    record.files['f3.pdf'] = {'description': 'Metadata only'}
    record.commit()
    db.session.commit()

    assert models.RecordFile.query.count() == 3
    assert FileInstance.query.count() == 2
    assert ObjectVersion.query.count() == 2
    assert Bucket.query.count() == 1
    assert len(record.files) == 3

    # Delete all files
    record.files.clear()
    record.commit()
    db.session.commit()

    assert models.RecordFile.query.count() == 0
    assert FileInstance.query.count() == 2
    assert ObjectVersion.query.count() == 4  # 2 original + 2 delete markers
    assert Bucket.query.count() == 1
    assert len(record.files) == 0
    assert 'f1.pdf' not in record.files
    assert 'f2.pdf' not in record.files
    assert 'f3.pdf' not in record.files
    assert record['files']['entries'] == {}
    assert record['files']['meta'] == {}


def test_record_files_store(base_app, db, location):
    """Test JSON stored for files."""
    record = Record.create({})

    # Add a file with bytes + metadata
    record.files['f1.pdf'] = (
        BytesIO(b'testfile'),
        {'description': 'Test file'}
    )
    # Add a file with only bytes
    record.files['f2.pdf'] = BytesIO(b'testfile')
    # Add a file with only metadata
    record.files['f3.pdf'] = {'description': 'Metadata only'}

    rf1 = record.files['f1.pdf']
    rf2 = record.files['f2.pdf']
    record.commit()
    assert record['files']['meta'] == {
        'f1.pdf': {'description': 'Test file'},
        'f2.pdf': None,
        'f3.pdf': {'description': 'Metadata only'},
    }
    assert record['files']['entries'] == {
        rf.key: {
            'bucket_id': str(record.bucket_id),
            'checksum': rf.file.checksum,
            'file_id': str(rf.file.file_id),
            'key': rf.key,
            'mimetype': rf.file.mimetype,
            'size': rf.file.size,
            'storage_class': rf.file.storage_class,
            'uri': rf.file.uri,
            'version_id': str(rf.object_version_id),
        } for rf in (rf1, rf2)
    }
