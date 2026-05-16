# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Check staged uploads release the DB connection during the upload."""

import io
import threading

import pytest
from sqlalchemy import event as sa_event
from sqlalchemy import text as sa_text

from tests.mock_module.api import RecordWithFiles


@pytest.fixture(scope="module")
def app_config(app_config):
    """Pin a real pool with one slot so a leaked checkout is visible."""
    app_config["RECORDS_RESOURCES_USE_STAGED_TRANSFER"] = True
    app_config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 1,
        "max_overflow": 0,
        "pool_timeout": 5,
    }
    return app_config


class _BlockingStream(io.RawIOBase):
    """Yields the first half, waits on ``release``, then yields the rest."""

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
    # We use the `database` fixture, not `db`, becasud `db` wraps the test in an outer
    # connection + savepoint, which holds a connection for the whole test and would mask
    # the DB connection release we're trying to observe.
    database,
    location,
    file_service,
    identity_simple,
):
    """Mid-upload, the staged path must hold zero pool connections."""
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
        finally:
            release.set()

        worker.join(timeout=15)
    finally:
        sa_event.remove(database.engine.pool, "checkout", _record_worker_checkout)

    assert not worker.is_alive(), "upload thread did not finish in time"
    assert (
        "error" not in upload_outcome
    ), f"upload failed: {upload_outcome.get('error')!r}"
    # The staged path opens two separate UoWs (setup + finalize); each one
    # checks out a connection. Together with the mid-upload assert above,
    # this confirms the pool is used before and after, but not during.
    assert worker_conn_checkouts >= 2, (
        f"staged path should check out a connection for setup and finalize; "
        f"saw {worker_conn_checkouts}"
    )

    file_service.commit_file(identity_simple, recid, "blocking.bin")

    with app.app_context():
        db_record = file_service.record_cls.pid.resolve(recid, registered_only=False)
        fi = db_record.files["blocking.bin"].object_version.file
        assert fi.readable is True
        assert fi.size == len(payload)
