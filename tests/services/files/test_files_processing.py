# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File service tests."""

from os.path import dirname, join
from unittest.mock import MagicMock

import pytest

from invenio_records_resources.services.files.components import processor
from invenio_records_resources.tasks import extract_file_metadata


@pytest.fixture()
def image_fp():
    """A test image."""
    with open(join(dirname(__file__), "testimage.png"), "rb") as fp:
        yield fp


def test_image_meta_extraction(
    file_service, location, example_record, identity_simple, image_fp, monkeypatch
):
    """Image metadata extraction."""
    # Patch celery task
    task = MagicMock()
    monkeypatch.setattr(processor, "extract_file_metadata", task)

    recid = example_record["id"]

    # Upload file
    file_service.init_files(identity_simple, recid, [{"key": "image.png"}])
    file_service.set_file_content(identity_simple, recid, "image.png", image_fp)

    # Commit (should send celery task)
    assert not task.apply_async.called
    file_service.commit_file(identity_simple, recid, "image.png")
    assert task.apply_async.called

    # Call task manually
    extract_file_metadata(*task.apply_async.call_args[1]["args"])

    item = file_service.read_file_metadata(identity_simple, recid, "image.png")
    assert item.data["metadata"] == {"width": 1000, "height": 1000}
