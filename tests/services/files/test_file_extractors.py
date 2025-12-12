# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File service tests."""

import pytest


@pytest.fixture()
def text_fp(tmp_path):
    """A test text file."""
    test_file = tmp_path / "testfile.txt"
    test_file.write_text("This is a dummy test file.\nLine 2: sample content.")
    with open(test_file, "rb") as fp:
        yield fp


def test_extractors_listing_extract_service(
    file_service, location, example_record, identity_simple, text_fp, search_clear
):
    """Test extraction API with a dummy extractor."""
    recid = example_record["id"]

    # Upload file
    file_service.init_files(identity_simple, recid, [{"key": "dummy.txt"}])
    file_service.set_file_content(identity_simple, recid, "dummy.txt", text_fp)

    file_service.commit_file(identity_simple, recid, "dummy.txt")

    listing = file_service.list_container(identity_simple, recid, "dummy.txt")
    assert listing.to_dict() == {
        "entries": [
            {
                "key": "dummy.txt",
                "size": 123456790,
                "links": {
                    "content": f"https://127.0.0.1:5000/api/mocks/{recid}/files/dummy.txt/container/dummy.txt"
                },
            }
        ],
        "folders": [],
        "total": 1,
        "truncated": False,
    }
    extracted = file_service.extract_container_item(
        identity_simple, recid, "dummy.txt", "dummy.txt"
    )

    extracted_data = extracted.send_file()
    assert (
        extracted_data.get_data(as_text=True) == "Contents of dummy.txt from dummy.txt"
    )

    opened = file_service.open_container_item(
        identity_simple, recid, "dummy.txt", "dummy.txt"
    )

    opened_data = opened.read()
    assert opened_data == "Contents of dummy.txt from dummy.txt"


def test_extractors_listing_service_with_links_template(
    file_service, location, example_record, identity_simple, text_fp, search_clear
):
    """Test extraction API with a dummy extractor."""
    recid = example_record["id"]

    # Upload file
    file_service.init_files(identity_simple, recid, [{"key": "dummy.txt"}])
    file_service.set_file_content(identity_simple, recid, "dummy.txt", text_fp)

    file_service.commit_file(identity_simple, recid, "dummy.txt")

    listing = file_service.list_container(identity_simple, recid, "dummy.txt")
    assert list(listing.entries) == [
        {
            "key": "dummy.txt",
            "size": 123456790,
            "links": {
                "content": f"https://127.0.0.1:5000/api/mocks/{recid}/files/dummy.txt/container/dummy.txt",
            },
        }
    ]
