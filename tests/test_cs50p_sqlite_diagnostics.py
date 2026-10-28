"""Event-controlled contention, safe observations and one admitted C16 job."""

import json
import logging
import multiprocessing
import sqlite3
import time

import pytest
from test_cs50_batch_worker import offline as offline
from test_cs50_batch_worker import scope as scope
from test_cs50p_mvp import download_args as download_args
from test_cs50p_native_admission import approval
from test_cs50p_native_admission import native as native
from test_cs50p_sqlite_stability import hold_uncommitted, stop_children

from scripts import cs50p_native as cli
from scripts.sqlite_contention_probe import Boundaries
from src.job_control.store import SQLITE_DIAGNOSTICS, Store


@pytest.fixture
def boundaries():
    handler = Boundaries()
    level, propagate = SQLITE_DIAGNOSTICS.level, SQLITE_DIAGNOSTICS.propagate
    SQLITE_DIAGNOSTICS.setLevel(logging.DEBUG)
    SQLITE_DIAGNOSTICS.propagate = False
    SQLITE_DIAGNOSTICS.addHandler(handler)
    try:
        yield handler
    finally:
        SQLITE_DIAGNOSTICS.removeHandler(handler)
        SQLITE_DIAGNOSTICS.setLevel(level)
        SQLITE_DIAGNOSTICS.propagate = propagate


@pytest.mark.parametrize("operation", ["heartbeat", "reinitialize"])
def test_held_writer_identifies_denied_begin_without_mutation(
    tmp_path, boundaries, operation
):
    store = Store(tmp_path / "private")
    store.heartbeat(42)
    context = multiprocessing.get_context("spawn")
    ready, release = context.Event(), context.Event()
    child = context.Process(target=hold_uncommitted, args=(store.path, ready, release))
    try:
        child.start()
        assert ready.wait(15)
        boundaries.events.clear()
        started = time.monotonic()
        with pytest.raises(sqlite3.OperationalError) as raised:
            if operation == "heartbeat":
                store.heartbeat(123)
            else:
                Store(store.root)
        assert raised.value.sqlite_errorcode == sqlite3.SQLITE_BUSY
        assert raised.value.job_db_phase == "begin"
        # Real timeout, not an injected SQLITE_BUSY or a changed busy handler.
        assert time.monotonic() - started >= 1.8
        stages = [event["stage"] for event in boundaries.events]
        assert "begin_wait" in stages and "begin_error" in stages
        assert "begin_ok" not in stages and "body" not in stages
        assert stages[-1] == "closed"
        assert all(not event["in_transaction"] for event in boundaries.events)
        # WAL reads proceed while the independently held write is uncommitted.
        with store.connection() as db:
            assert db.execute("SELECT heartbeat FROM worker").fetchone() == (42,)
        # Abort the holder; neither its write nor the denied heartbeat may persist.
        child.kill()
        child.join(timeout=5)
        reopened = Store(store.root)
        with reopened.connection() as db:
            assert db.execute("SELECT heartbeat FROM worker").fetchone() == (42,)
            assert db.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert not (store.root / "quarantine").exists()
    finally:
        stop_children([child])


def test_boundaries_exclude_sql_paths_values_and_exception_text(tmp_path, boundaries):
    store = Store(tmp_path / "PRIVATE_PATH")
    boundaries.events.clear()
    with pytest.raises(sqlite3.OperationalError):
        with store.connection(write=True) as db:
            db.execute("INSERT INTO worker VALUES(1,123456789)")
            db.execute("SELECT PRIVATE_VALUE FROM PRIVATE_TABLE")
    events = boundaries.events
    assert [event["stage"] for event in events] == [
        "opened",
        "begin_wait",
        "begin_ok",
        "body",
        "body_error",
        "rollback_ok",
        "close_wait",
        "closed",
    ]
    encoded = json.dumps(events)
    for private in (
        "PRIVATE_PATH",
        "PRIVATE_VALUE",
        "PRIVATE_TABLE",
        "INSERT",
        str(store.path),
    ):
        assert private not in encoded
    allowed = {
        "pid",
        "tid",
        "started_ns",
        "at_ns",
        "cpu_ns",
        "attempt",
        "write",
        "stage",
        "in_transaction",
        "sqlite_code",
        "operation",
        "cycle",
    }
    assert all(set(event) == allowed for event in events)
    assert all(
        a["at_ns"] <= b["at_ns"] for a, b in zip(events, events[1:], strict=False)
    )
    assert events[4]["sqlite_code"] == sqlite3.SQLITE_ERROR
    with store.connection() as db:
        assert db.execute("SELECT * FROM worker").fetchall() == []


def test_disabled_or_failed_observation_does_not_change_commit(tmp_path, monkeypatch):
    store = Store(tmp_path / "private")

    def broken(*args, **kwargs):
        raise RuntimeError("Observer unavailable")

    monkeypatch.setattr(SQLITE_DIAGNOSTICS, "debug", broken)
    monkeypatch.setattr(SQLITE_DIAGNOSTICS, "isEnabledFor", lambda _: False)
    store.heartbeat(41)
    monkeypatch.setattr(SQLITE_DIAGNOSTICS, "isEnabledFor", lambda _: True)
    store.heartbeat(42)
    with store.connection() as db:
        assert db.execute("SELECT heartbeat FROM worker").fetchone() == (42,)


def status_reader(settings_json, job_id, ready, stop, report):
    from src.job_control.models import Settings

    settings = Settings.model_validate_json(settings_json)
    reads = 0
    try:
        while not stop.is_set():
            assert cli.status(settings, job_id).job_id == job_id
            reads += 1
            ready.set()
            stop.wait(0.1)  # Bounded 10-Hz reconnecting client, no writer loop.
        report.put(dict(reads=reads, failed=False))
    except Exception:
        report.put(dict(reads=reads, failed=True))


def test_one_native_job_with_independent_ten_hz_status_client(native):
    settings = native["settings"]
    assert settings.max_parallel == settings.max_queued == 1
    grant = approval(native, workflow="sqlite_one_job")
    context = multiprocessing.get_context("spawn")
    ready, stop, report = context.Event(), context.Event(), context.Queue()
    reader = context.Process(
        target=status_reader,
        args=(
            settings.model_dump_json(),
            grant["job_id"],
            ready,
            stop,
            report,
        ),
    )
    try:
        reader.start()
        assert ready.wait(15)
        result = cli.run(settings, native["limits"], grant["job_id"], offline_test=True)
        assert result.status == "completed" and result.exit_code == 0
        stop.set()
        reader.join(timeout=10)
        assert reader.exitcode == 0
        observation = report.get(timeout=2)
        assert not observation["failed"] and observation["reads"] >= 2
        assert cli.result(settings, grant["job_id"])["report"]["status"] == "completed"
        store = Store(settings.root)
        assert len(store.all()) == 1
        with store.connection() as db:
            assert db.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert not (settings.root / "quarantine").exists()
        with pytest.raises(PermissionError):
            cli.run(settings, native["limits"], grant["job_id"], offline_test=True)
    finally:
        stop.set()
        stop_children([reader])
        report.close()
        report.join_thread()
