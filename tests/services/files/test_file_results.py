# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File results tests."""

import pytest

from invenio_records_resources.services.files.results import FileItem, FileList


@pytest.fixture(scope='function')
def file_entry():
    return {
        "created": "2020-11-15T19:04:22",
        "updated": "2020-11-15T19:04:22",
        "key": "article.pdf",
        "checksum": "md5:abcdef...",
        "size": 2048,
        "metadata": {
            "description": "Published article PDF.",
        },
        "links": {}
    }


@pytest.mark.skip()
def test_file_item_result(service, identity_simple, file_entry,
                          example_record):
    """Test the file item result.

    NOTE: `links` is an empty dictionary, it's contents are tested at resource
          level, since it is config dependent. Here the default
          `links_config=None` is tested.
    """
    item = FileItem(service, identity_simple, file_entry,
                    example_record, links_config=None)
    result = item.to_dict()

    assert result == file_entry


@pytest.mark.skip()
def test_file_list_result(service, identity_simple, file_entry,
                          example_record):
    """Test the file item result.

    NOTE: `links` is an empty dictionary, it's contents are tested at resource
          level, since it is config dependent. Here the default
          `links_config=None` is tested.
    """
    entries = [file_entry, file_entry]
    list_ = FileList(service, identity_simple, entries, links_config=None)
    result = list_.to_dict()

    assert result == {"entries": entries}
