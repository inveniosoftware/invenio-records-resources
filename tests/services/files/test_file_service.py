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
from marshmallow import ValidationError


def test_file_flow(
        file_service, location, example_file_record, identity_simple):
    """Test the lifecycle of a file.

    - Initialize file saving
    - Save 1 files
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
        recid, 'article.txt', identity_simple)
    assert result.file_id == 'article.txt'

    # Assert deleted
    result = file_service.list_files(recid, identity_simple)
    assert result.entries
    assert len(list(result.entries)) == 0

    # Delete all remaining files
    result = file_service.delete_all_files(recid, identity_simple)
    assert list(result.entries) == []


def test_init_files(
        file_service, location, example_file_record, identity_simple):

    recid = example_file_record['id']

    # Pass an object with missing required field
    file_to_initialise = [{}]

    with pytest.raises(ValidationError) as e:
        file_service.init_files(recid, identity_simple, file_to_initialise)

    error = e.value
    assert (
        {0: {'key': ['Missing data for required field.']}} ==
        error.normalized_messages()
    )

    # Pass an object with added field
    file_to_initialise = [{
        'key': 'article.txt',
        'foo': 'bar',
    }]

    result = file_service.init_files(
        recid, identity_simple, file_to_initialise)

    entry = result.to_dict()['entries'][0]
    assert file_to_initialise[0]['key'] == entry['key']
    assert file_to_initialise[0]['foo'] == entry['metadata']['foo']
