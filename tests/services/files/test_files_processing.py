# SPDX-FileCopyrightText: 2021 CERN.
# SPDX-FileCopyrightText: 2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

"""File service tests."""

from io import BytesIO
from os.path import dirname, join
from unittest.mock import MagicMock

import pytest

from invenio_records_resources.services.errors import InvalidFileContentError
from invenio_records_resources.services.files.components import processor
from invenio_records_resources.services.files.extractors.zip import ZipExtractor
from invenio_records_resources.services.files.processors.zip import ZipProcessor
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


def test_zip_meta_extraction(
    file_service, location, example_record, identity_simple, zip_fp, monkeypatch
):
    """Image metadata extraction."""
    # Patch celery task
    task = MagicMock()
    monkeypatch.setattr(processor, "extract_file_metadata", task)

    recid = example_record["id"]

    # Upload file
    file_service.init_files(identity_simple, recid, [{"key": "testzip.zip"}])
    file_service.set_file_content(identity_simple, recid, "testzip.zip", zip_fp)

    # Commit (should send celery task)
    assert not task.apply_async.called
    file_service.commit_file(identity_simple, recid, "testzip.zip")
    assert task.apply_async.called

    # Call task manually
    extract_file_metadata(*task.apply_async.call_args[1]["args"])

    item = file_service.read_file_metadata(identity_simple, recid, "testzip.zip")
    assert item.data["metadata"] == {"zip_toc_position": 236}


@pytest.mark.parametrize("invalid_content", ["non-zip", "truncated"])
def test_invalid_zip_metadata(zip_fp, invalid_content):
    """Persist malformed ZIP errors so listing rejects them consistently."""
    content = b"not a ZIP file" if invalid_content == "non-zip" else zip_fp.read()[:-22]
    file_record = MagicMock(key="archive.zip", metadata={"description": "Archive"})
    file_record.open_stream.return_value = BytesIO(content)

    ZipProcessor().process(file_record)

    assert file_record.metadata["description"] == "Archive"
    assert file_record.metadata["error"]
    assert "zip_toc_position" not in file_record.metadata
    with pytest.raises(InvalidFileContentError):
        ZipExtractor().list(file_record)


def test_zip_processor_unexpected_error():
    """Do not save unexpected storage failures as archive-validation errors."""
    file_record = MagicMock(metadata={})
    file_record.open_stream.side_effect = OSError("Storage unavailable")

    with pytest.raises(OSError, match="Storage unavailable"):
        ZipProcessor().process(file_record)
    assert file_record.metadata == {}
