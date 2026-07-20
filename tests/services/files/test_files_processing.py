# SPDX-FileCopyrightText: 2021 CERN.
# SPDX-License-Identifier: MIT

"""File service tests."""

from os.path import dirname, join
from unittest.mock import ANY, MagicMock, call

import pytest
from invenio_pidstore.errors import PIDDoesNotExistError
from sqlalchemy.orm.exc import NoResultFound

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


@pytest.mark.parametrize(
    ("service_id", "fallback_service_id", "error"),
    [
        ("draft-files", "files", NoResultFound()),
        (
            "draft-media-files",
            "media-files",
            PIDDoesNotExistError("recid", "record-id"),
        ),
    ],
)
def test_extraction_uses_published_fallback(
    service_id, fallback_service_id, error, monkeypatch
):
    """Retry through the matching published service when the draft is gone."""
    draft_service = MagicMock()
    draft_service.extract_file_metadata.side_effect = error
    published_service = MagicMock()
    registry = MagicMock()
    registry.get.side_effect = {
        service_id: draft_service,
        fallback_service_id: published_service,
    }.get
    monkeypatch.setattr(
        "invenio_records_resources.tasks.current_service_registry",
        registry,
    )

    extract_file_metadata(service_id, "record-id", "test.zip")

    assert registry.get.call_args_list == [call(service_id), call(fallback_service_id)]
    published_service.extract_file_metadata.assert_called_once_with(
        ANY, "record-id", "test.zip"
    )


def test_extraction_logs_file_context(monkeypatch):
    """Log the affected file and original processor error."""
    service = MagicMock()
    service.extract_file_metadata.side_effect = RuntimeError("processor failed")
    registry = MagicMock()
    registry.get.return_value = service
    app = MagicMock()
    monkeypatch.setattr(
        "invenio_records_resources.tasks.current_service_registry",
        registry,
    )
    monkeypatch.setattr("invenio_records_resources.tasks.current_app", app)

    extract_file_metadata("draft-files", "record-id", "test.zip")

    app.logger.exception.assert_called_once_with(
        "Failed to extract file metadata. service_id=%s record_id=%s "
        "file_key=%s exception_type=%s exception=%s",
        "draft-files",
        "record-id",
        "test.zip",
        "RuntimeError",
        service.extract_file_metadata.side_effect,
    )
