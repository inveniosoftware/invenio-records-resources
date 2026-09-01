# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Test database connection use during uploads."""

import io
import threading

import pytest
from sqlalchemy import event as sa_event
from sqlalchemy import text as sa_text

from invenio_records_resources.services.errors import TransferException
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


def test_staged_upload_releases_db_connection(
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

            with pytest.raises(TransferException, match="already been claimed"):
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
