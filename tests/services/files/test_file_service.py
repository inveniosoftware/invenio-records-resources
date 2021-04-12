# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File service tests."""

from io import BytesIO

import pytest


@pytest.mark.skip()
def test_file_flow(
        file_service, location, example_file_record, identity_simple):
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
    recid = example_file_record['id']
    file_to_initialise = [{
        'key': 'article.txt',
        'checksum': 'md5:c785060c866796cc2a1708c997154c8e',
        'size': 17,  # 2kB
        'metadata': {
            'description': 'Published article PDF.',
        }
    }]
    # Initialize file saving
    result = file_service.init_files(
        recid, identity_simple, file_to_initialise)
    assert result.to_dict()['entries'][0]['key'] == \
        file_to_initialise[0]['key']
    # # Save 3 files
    # to_files = ['one', 'two', 'three']

    # for to_file in to_files:
    content = BytesIO(b'test file content')
    result = file_service.set_file_content(
        recid, file_to_initialise[0]['key'], identity_simple, content,
        content.getbuffer().nbytes
    )
    # TODO figure response for succesfully saved file
    assert result.to_dict()['key'] == file_to_initialise[0]['key']

    result = file_service.commit_file(
        recid, 'article.txt', identity_simple)
    # TODO currently there is no status in the json between the initialisation
    # and the commiting.
    assert result.to_dict()['key'] == \
        file_to_initialise[0]['key']

    # List files
    result = file_service.list_files(recid, identity_simple)
    assert result.to_dict()['entries'][0]['key'] == \
        file_to_initialise[0]['key']

    # Read file metadata
    result = file_service.read_file_metadata(
        recid, 'article.txt', identity_simple)
    assert result.to_dict()['key'] == \
        file_to_initialise[0]['key']

    # Retrieve file
    result = file_service.get_file_content(
        recid, 'article.txt', identity_simple)
    assert result.file_id == 'article.txt'

    # Delete file
    result = file_service.delete_file(
        recid, 'article.txt', identity_simple, 0)
    assert result.file_id == 'article.txt'

    # Assert deleted
    result = file_service.list_files(recid, identity_simple)
    assert result.files
    assert not result.files.get('article.txt')

    # Delete all remaining files
    result = file_service.delete_all_files(recid, identity_simple)
    assert result.files == {}

    # Assert deleted
    result = file_service.list_files(recid, identity_simple)
    assert result.files == {}


@pytest.mark.skip()
def test_read_not_commited_file(service, example_record, identity_simple):
    recid = example_record.id
    file_id = 'file.txt'
    result = _add_file_to_record(recid, file_id, identity_simple, service)

    # Read, should allow to get metadata
    result = service.read_file_metadata(recid, file_id, identity_simple)
    assert result.file_id == 'file_one.txt'


@pytest.mark.skip()
def test_retrieve_not_commited_file(service, example_record, identity_simple):
    recid = example_record.id
    file_id = 'file.txt'
    result = _add_file_to_record(recid, file_id, identity_simple, service)

    # Retrieve, should not exist
    result = service.retrieve_file(recid, file_id, identity_simple)
    assert not result


@pytest.mark.skip()
def test_delete_not_commited_file(service, example_record, identity_simple):
    recid = example_record.id
    file_id = 'file.txt'
    result = _add_file_to_record(recid, file_id, identity_simple, service)

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


@pytest.mark.skip()
def test_read_deleted_file(service, example_record, identity_simple):
    recid = example_record.id
    file_id = 'file.txt'
    result = _commit_delete_file(recid, file_id, identity_simple, service)

    # Read, should not exist
    result = service.read_file_metadata(recid, file_id, identity_simple)
    assert not result


@pytest.mark.skip()
def test_retrieve_deleted_file(service, example_record, identity_simple):
    recid = example_record.id
    file_id = 'file.txt'
    result = _commit_delete_file(recid, file_id, identity_simple, service)

    # Read, should not exist
    result = service.retrieve_file(recid, file_id, identity_simple)
    assert not result
