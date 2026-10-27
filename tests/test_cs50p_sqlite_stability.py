"""Synthetic process contention and crash boundaries; no production databases."""

import multiprocessing
import sqlite3
import time

import pytest

from src.job_control.store import Store


def competing_writer(root, barrier, report, cycles, pause):
    operation, index, started = "initialize", -1, time.monotonic()
    try:
        store = Store(root)
        barrier.wait(timeout=15)
        for index in range(cycles):
            operation, started = "increment", time.monotonic()
            with store.connection(write=True) as db:
                db.execute("UPDATE worker SET heartbeat=heartbeat+1 WHERE id=1")
            if index % 16 == 0:
                operation, started = "reinitialize", time.monotonic()
                store = Store(root)
            if pause:
                time.sleep(pause)
        report.put(None)
    except Exception as error:
        report.put(
            (
                operation,
                index,
                time.monotonic() - started,
                type(error).__name__,
                getattr(error, "sqlite_errorcode", None),
                getattr(error, "job_db_phase", None),
            )
        )


def hold_uncommitted(path, ready, release):
    db = sqlite3.connect(path, timeout=2)
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE worker SET heartbeat=999 WHERE id=1")
        ready.set()
        if release.wait(15):
            db.commit()
    finally:
        db.close()


def stop_children(children):
    for child in children:
        if child.is_alive():
            child.terminate()
        if child.pid is not None:
            child.join(timeout=5)
        assert not child.is_alive()


@pytest.mark.parametrize("cycles", [64, 300])
@pytest.mark.parametrize("pause", [0, 0.01])
def test_three_independent_writers_with_pinned_wal_reader(tmp_path, cycles, pause):
    store = Store(tmp_path / "private")
    store.heartbeat(0)
    context = multiprocessing.get_context("spawn")
    barrier, report = context.Barrier(3), context.Queue()
    children = [
        context.Process(
            target=competing_writer, args=(store.root, barrier, report, cycles, pause)
        )
        for _ in range(3)
    ]
    try:
        with store.connection() as reader:
            reader.execute("BEGIN")
            assert reader.execute("SELECT heartbeat FROM worker").fetchone() == (0,)
            for child in children:
                child.start()
            for child in children:
                child.join(timeout=90)
            assert [c.exitcode for c in children] == [0] * 3
            assert [report.get(timeout=2) for _ in children] == [None] * 3
            # WAL readers retain their old snapshot without blocking commits.
            assert reader.execute("SELECT heartbeat FROM worker").fetchone() == (0,)
        with store.connection() as db:
            assert db.execute("SELECT heartbeat FROM worker").fetchone() == (
                3 * cycles,
            )
            assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert db.execute("PRAGMA journal_mode").fetchone() == ("wal",)
        assert not (store.root / "quarantine").exists()
    finally:
        stop_children(children)
        report.close()
        report.join_thread()


def test_killed_writer_rolls_back_before_process_restart(tmp_path):
    store = Store(tmp_path / "private")
    store.heartbeat(42)
    context = multiprocessing.get_context("spawn")
    ready, release = context.Event(), context.Event()
    child = context.Process(target=hold_uncommitted, args=(store.path, ready, release))
    try:
        child.start()
        assert ready.wait(15)
        with store.connection() as db:
            assert db.execute("SELECT heartbeat FROM worker").fetchone() == (42,)
        child.kill()
        child.join(timeout=5)
        assert child.exitcode == -9
        reopened = Store(store.root)
        with reopened.connection(write=True) as db:
            assert db.execute("SELECT heartbeat FROM worker").fetchone() == (42,)
            db.execute("UPDATE worker SET heartbeat=43")
        with reopened.connection() as db:
            assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    finally:
        stop_children([child])


def test_multiprocess_persistent_writer_denies_begin_without_body(tmp_path):
    store = Store(tmp_path / "private")
    store.heartbeat(42)
    context = multiprocessing.get_context("spawn")
    ready, release = context.Event(), context.Event()
    child = context.Process(target=hold_uncommitted, args=(store.path, ready, release))
    try:
        child.start()
        assert ready.wait(15)
        with pytest.raises(sqlite3.OperationalError) as raised:
            with store.connection(write=True):
                pytest.fail("Busy writer must never enter the transaction body")
        assert raised.value.sqlite_errorcode == sqlite3.SQLITE_BUSY
        assert raised.value.job_db_phase == "begin"
        release.set()
        child.join(timeout=10)
        assert child.exitcode == 0
        with store.connection() as db:
            assert db.execute("SELECT heartbeat FROM worker").fetchone() == (999,)
    finally:
        stop_children([child])
