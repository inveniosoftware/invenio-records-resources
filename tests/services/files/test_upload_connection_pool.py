# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Test database connection use during uploads."""

import io
import os
import threading

import pytest
from invenio_files_rest.models import FileInstance
from sqlalchemy import event as sa_event
from sqlalchemy import text as sa_text

from invenio_records_resources.services.errors import TransferException
from invenio_records_resources.services.files.upload import (
    FileUpload,
    UploadSuperseded,
)
from tests.mock_module.api import RecordWithFiles


@pytest.fixture(scope="module")
def app_config(app_config):
    """Configure a single-connection pool."""
    app_config["RECORDS_RESOURCES_USE_STAGED_TRANSFER"] = True
    app_config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 1,
        "max_overflow": 0,
        "pool_timeout": 5,
    }
    return app_config


class _BlockingStream(io.RawIOBase):
    """Pause between two chunks."""

    def __init__(self, data, blocked, release):
        midpoint = len(data) // 2
        self._chunks = [data[:midpoint], data[midpoint:]]
        self._next_chunk = 0
        self._blocked = blocked
        self._release = release

    def readable(self):
        return True

    def read(self, n=-1):
        if self._next_chunk >= len(self._chunks):
            return b""
        if self._next_chunk == 1:
            self._blocked.set()
            assert self._release.wait(timeout=10), "release event was never set"
        chunk = self._chunks[self._next_chunk]
        self._next_chunk += 1
        return chunk


def test_upload_releases_db_connection_while_streaming(
    app,
    # The db fixture holds a connection for the full test, hiding leaks.
    database,
    location,
    file_service,
    identity_simple,
):
    """Release the database connection while content is streaming."""
    with app.app_context():
        record = RecordWithFiles.create({}, metadata={"title": "pool-test"})
        record["files"] = {"enabled": True}
        record.commit()
        database.session.commit()
        recid = record["id"]

    file_service.init_files(identity_simple, recid, [{"key": "blocking.bin"}])

    payload = b"a" * 4096
    blocked = threading.Event()
    release = threading.Event()
    upload_outcome = {}

    def _run_upload():
        with app.app_context():
            try:
                upload_outcome["result"] = file_service.set_file_content(
                    identity_simple,
                    recid,
                    "blocking.bin",
                    _BlockingStream(payload, blocked, release),
                    len(payload),
                )
            except Exception as exc:
                upload_outcome["error"] = exc

    worker_conn_checkouts = 0

    def _record_worker_checkout(*args, **kwargs):
        nonlocal worker_conn_checkouts
        if threading.current_thread().name == "staged-upload":
            worker_conn_checkouts += 1

    sa_event.listen(database.engine.pool, "checkout", _record_worker_checkout)
    try:
        worker = threading.Thread(target=_run_upload, name="staged-upload")
        worker.start()

        try:
            assert blocked.wait(timeout=10), "upload did not enter mid-stream wait"
            assert database.engine.pool.checkedout() == 0
            with database.engine.connect() as conn:
                assert conn.execute(sa_text("SELECT 1")).scalar() == 1

            with pytest.raises(TransferException, match="is already being uploaded"):
                file_service.set_file_content(
                    identity_simple,
                    recid,
                    "blocking.bin",
                    io.BytesIO(b"losing upload"),
                    len(b"losing upload"),
                )
        finally:
            release.set()

        worker.join(timeout=15)
    finally:
        sa_event.remove(database.engine.pool, "checkout", _record_worker_checkout)

    assert not worker.is_alive(), "upload thread did not finish in time"
    assert (
        "error" not in upload_outcome
    ), f"upload failed: {upload_outcome.get('error')!r}"
    assert (
        worker_conn_checkouts >= 2
    ), f"expected setup and finalize checkouts, saw {worker_conn_checkouts}"

    file_service.commit_file(identity_simple, recid, "blocking.bin")

    with app.app_context():
        db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
        fi = db_record.files["blocking.bin"].object_version.file
        assert fi.readable is True
        assert fi.size == len(payload)


def _create_record(app, database, title):
    """Create an empty record with files enabled."""
    with app.app_context():
        record = RecordWithFiles.create({}, metadata={"title": title})
        record["files"] = {"enabled": True}
        record.commit()
        database.session.commit()
        return record["id"]


def test_superseded_upload_cleans_up_only_its_own_rows(
    app,
    database,
    location,
    file_service,
    identity_simple,
    monkeypatch,
):
    """Clean up the superseded upload without touching the file that replaced it."""
    recid = _create_record(app, database, "race-finalize")
    file_service.init_files(identity_simple, recid, [{"key": "raced.bin"}])

    blocked = threading.Event()
    release = threading.Event()
    original_finalize = FileUpload._finalize
    waited = threading.Event()

    def _blocking_finalize(self, *args, **kwargs):
        # Hold the superseded upload between the storage write and the finalize.
        if threading.current_thread().name == "staged-upload" and not waited.is_set():
            waited.set()
            blocked.set()
            assert release.wait(timeout=10), "release event was never set"
        return original_finalize(self, *args, **kwargs)

    monkeypatch.setattr(FileUpload, "_finalize", _blocking_finalize)

    payload = b"b" * 4096
    outcome = {}

    def _run_upload():
        with app.app_context():
            try:
                outcome["result"] = file_service.set_file_content(
                    identity_simple,
                    recid,
                    "raced.bin",
                    io.BytesIO(payload),
                    len(payload),
                )
            except Exception as exc:
                outcome["error"] = exc

    upload_thread = threading.Thread(target=_run_upload, name="staged-upload")
    upload_thread.start()

    replacement_content = b"winning upload"
    try:
        assert blocked.wait(timeout=10), "upload did not reach the finish step"

        with app.app_context():
            superseded_file_instance = (
                file_service.record_cls.pid.resolve(recid, registered_only=False)
                .files["raced.bin"]
                .object_version.file
            )
            superseded_file_instance_id = superseded_file_instance.id
            superseded_uri = superseded_file_instance.uri

            # Delete the pending upload and re-initialize the same key, so the
            # blocked upload no longer holds the rows it reserved.
            file_service.delete_file(identity_simple, recid, "raced.bin")
            file_service.init_files(identity_simple, recid, [{"key": "raced.bin"}])
            file_service.set_file_content(
                identity_simple,
                recid,
                "raced.bin",
                io.BytesIO(replacement_content),
                len(replacement_content),
            )
            file_service.commit_file(identity_simple, recid, "raced.bin")
    finally:
        release.set()

    upload_thread.join(timeout=15)
    assert not upload_thread.is_alive(), "upload thread did not finish in time"
    assert isinstance(
        outcome.get("error"), UploadSuperseded
    ), f"expected the superseded upload to fail, got {outcome!r}"

    with app.app_context():
        current_file_instance = (
            file_service.record_cls.pid.resolve(recid, registered_only=False)
            .files["raced.bin"]
            .object_version.file
        )
        assert current_file_instance.id != superseded_file_instance_id
        assert current_file_instance.readable is True
        assert current_file_instance.size == len(replacement_content)

        # The losing upload removed its own row and its own bytes, nothing else.
        assert (
            FileInstance.query.filter_by(id=superseded_file_instance_id).one_or_none()
            is None
        )
        assert not os.path.exists(superseded_uri)
        assert os.path.exists(current_file_instance.uri)


def test_upload_aborts_when_storage_fails_mid_stream(
    app,
    database,
    location,
    file_service,
    identity_simple,
):
    """Abort and clean up when the storage write raises an unexpected error."""
    recid = _create_record(app, database, "race-stream")
    file_service.init_files(identity_simple, recid, [{"key": "yanked.bin"}])

    blocked = threading.Event()
    release = threading.Event()
    outcome = {}

    def _run_upload():
        with app.app_context():
            try:
                outcome["result"] = file_service.set_file_content(
                    identity_simple,
                    recid,
                    "yanked.bin",
                    _BlockingStream(b"c" * 4096, blocked, release),
                    4096,
                )
            except Exception as exc:
                outcome["error"] = exc

    upload_thread = threading.Thread(target=_run_upload, name="staged-upload")
    upload_thread.start()

    try:
        assert blocked.wait(timeout=10), "upload did not enter mid-stream wait"
        with app.app_context():
            superseded_file_instance = (
                file_service.record_cls.pid.resolve(recid, registered_only=False)
                .files["yanked.bin"]
                .object_version.file
            )
            superseded_file_instance_id = superseded_file_instance.id
            # Deleting the pending upload takes the storage out from under the
            # in-flight write, so `storage.save` raises mid-stream.
            file_service.delete_file(identity_simple, recid, "yanked.bin")
    finally:
        release.set()

    upload_thread.join(timeout=15)
    assert not upload_thread.is_alive(), "upload thread did not finish in time"
    assert "error" in outcome, "expected the interrupted upload to fail"

    with app.app_context():
        db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
        assert "yanked.bin" not in db_record.files
        assert (
            FileInstance.query.filter_by(id=superseded_file_instance_id).one_or_none()
            is None
        )
