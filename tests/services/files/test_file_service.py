# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File service tests."""

from io import BytesIO


def test_file_flow(service, example_record, identity_simple):
    """Test the lifecycle of a file.

    - Initialize file saving
    - Save 3 files
    - Commit the files
    - List files of the record
    - Read file metadata
    - Retrieve a file
    - Delete a file
    - Delete all remaining files
    - List should be empty
    """
    recid = example_record.id

    # Initialize file saving
    result = service.init_file(recid, identity_simple, data={})
    assert result.files

    # Save 3 files
    to_files = ["one", "two", "three"]

    for to_file in to_files:
        content = f"test file content {to_file}"
        result = service.save_file(
            recid, f"file_{to_file}.txt", identity_simple,
            BytesIO(bytes(content, "utf-8"))
        )
        assert result.files.get(f"file_{to_file}.txt")

        result = service.commit_file(
            recid, f"file_{to_file}.txt", identity_simple)
        assert result.files.get(f"file_{to_file}.txt")

    # List files
    result = service.list_files(recid, identity_simple)
    assert result.files
    for to_file in to_files:
        assert result.files.get(f"file_{to_file}.txt")

    # Read file metadata
    result = service.read_file_metadata(
        recid, "file_one.txt", identity_simple)
    assert result.file_id == "file_one.txt"

    # Retrieve file
    result = service.retrieve_file(
        recid, "file_one.txt", identity_simple)
    assert result.file_id == "file_one.txt"

    # Delete file
    result = service.delete_file(
        recid, "file_one.txt", identity_simple, 0)
    assert result.file_id == "file_one.txt"

    # Assert deleted
    result = service.list_files(recid, identity_simple)
    assert result.files
    assert not result.files.get(f"file_one.txt")

    # Delete all remaining files
    result = service.delete_all_files(recid, identity_simple)
    assert result.files == {}

    # Assert deleted
    result = service.list_files(recid, identity_simple)
    assert result.files == {}


def _init_save_file(recid, file_id, identity, service):
    # Initialize file saving
    result = service.init_file(recid, identity, data={})
    assert result.files
    result = service.save_file(
        recid, file_id, identity, BytesIO(b"test file content"))
    assert result.files.get(file_id)

    return result


def test_read_not_commited_file(service, example_record, identity_simple):
    recid = example_record.id
    file_id = "file.txt"
    result = _init_save_file(recid, file_id, identity_simple, service)

    # Read, should allow to get metadata
    result = service.read_file_metadata(recid, file_id, identity_simple)
    assert result.file_id == "file_one.txt"


def test_retrieve_not_commited_file(service, example_record, identity_simple):
    recid = example_record.id
    file_id = "file.txt"
    result = _init_save_file(recid, file_id, identity_simple, service)

    # Retrieve, should not exist
    result = service.retrieve_file(recid, file_id, identity_simple)
    assert not result


def test_delete_not_commited_file(service, example_record, identity_simple):
    recid = example_record.id
    file_id = "file.txt"
    result = _init_save_file(recid, file_id, identity_simple, service)

    # Delete, should work
    result = service.delete_file(recid, file_id, identity_simple)
    assert result

    # Read, should not exist
    result = service.read_file_metadata(recid, file_id, identity_simple)
    assert not result


def _commit_delete_file(recid, file_id, identity, service):
    result = _init_save_file(recid, file_id, identity, service)

    # Commit file
    result = service.commit_file(recid, file_id, identity)
    assert result.files.get(file_id)
    # Delete file
    result = service.delete_file(recid, file_id, identity)
    assert result

    return result


def test_read_deleted_file(service, example_record, identity_simple):
    recid = example_record.id
    file_id = "file.txt"
    result = _commit_delete_file(recid, file_id, identity_simple, service)

    # Read, should not exist
    result = service.read_file_metadata(recid, file_id, identity_simple)
    assert not result


def test_retrieve_deleted_file(service, example_record, identity_simple):
    recid = example_record.id
    file_id = "file.txt"
    result = _commit_delete_file(recid, file_id, identity_simple, service)

    # Read, should not exist
    result = service.retrieve_file(recid, file_id, identity_simple)
    assert not result
