"""Independent process connections, WAL churn and deterministic cancel ordering."""

import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import pytest
from test_job_control import request_data
from test_job_control import setup as setup

from src.job_control.models import Artifact
from src.job_control.store import Store


def churn(root, barrier, report, writer, cycles=64):
    operation = "initialize"
    try:
        store = Store(root)
        barrier.wait(timeout=10)
        for index in range(cycles):
            operation = "heartbeat" if writer else "read"
            if writer:
                store.heartbeat(index)
            else:
                assert store.all() == ()
                store.worker_available(10)
            if index % 10 == 0:
                operation = "reinitialize"
                store = Store(root)
        report.put(None)
    except Exception as error:
        report.put(
            (operation, type(error).__name__, getattr(error, "sqlite_errorcode", None))
        )


def test_independent_process_readers_writer_and_reinitialization(tmp_path):
    store = Store(tmp_path / "private")
    context = multiprocessing.get_context("spawn")
    barrier, report = context.Barrier(4), context.Queue()
    children = [
        context.Process(target=churn, args=(store.root, barrier, report, index == 0))
        for index in range(4)
    ]
    try:
        for child in children:
            child.start()
        for child in children:
            child.join(timeout=30)
        assert [c.exitcode for c in children] == [0] * 4
        assert [report.get(timeout=1) for _ in children] == [None] * 4
        with store.connection() as db:
            assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert db.execute("PRAGMA journal_mode").fetchone() == ("wal",)
            assert db.execute("SELECT heartbeat FROM worker").fetchone() == (63,)
        assert not (store.root / "quarantine").exists()
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
            if child.pid:
                child.join(timeout=5)
        report.close()
        report.join_thread()


@pytest.mark.parametrize("first_status", ["cancel_requested", "completed"])
def test_cancel_and_completion_use_committed_state_under_concurrent_writers(
    setup, monkeypatch, first_status
):
    env = setup
    job = env.controller.create(
        env.actor, request_data(env) | {"start": False}, "synthetic_concurrent_finish"
    )
    first = env.controller.store
    first.transition(job.job_id, "queued", "queued", "Synthetic release")
    first.transition(job.job_id, "running", "running", "Synthetic execution")
    second = Store(env.settings.root)
    artifact = Artifact(
        artifact_id="synthetic_artifact",
        job_id=job.job_id,
        kind="material_plan",
        size_bytes=1,
        sha256="a" * 64,
        created_at=job.created_at,
        input_refs=job.input_refs,
    )
    completed = dict(
        exit_code=0, artifact_refs=(artifact,), output_refs=(artifact.artifact_id,)
    )
    held, contender, release = threading.Event(), threading.Event(), threading.Event()
    put = first.put_db

    def hold_commit(db, changed, message):
        put(db, changed, message)
        held.set()
        assert release.wait(10)

    original = second.connection

    @contextmanager
    def competing_connection(write=False):
        contender.set()
        with original(write=write) as db:
            yield db

    monkeypatch.setattr(first, "put_db", hold_commit)
    monkeypatch.setattr(second, "connection", competing_connection)
    following = (
        "completed" if first_status == "cancel_requested" else "cancel_requested"
    )
    with ThreadPoolExecutor(max_workers=2) as threads:
        winner = threads.submit(
            first.transition,
            job.job_id,
            first_status,
            first_status,
            "Synthetic first commit",
            **(completed if first_status == "completed" else {}),
        )
        try:
            if not held.wait(10):
                winner.result(timeout=1)
                pytest.fail("First writer never reached its commit barrier")
            follower = threads.submit(
                second.transition,
                job.job_id,
                following,
                following,
                "Synthetic competing commit",
                **(completed if following == "completed" else {}),
            )
            assert contender.wait(10)
        finally:
            release.set()
        winner.result(timeout=10)
        result = follower.result(timeout=10)
    expected = "cancelled" if first_status == "cancel_requested" else "completed"
    assert result.status == expected == second.get(job.job_id).status
    assert not result.cancellable
    assert (
        second.transition(job.job_id, "running", "running", "Must not restart")
        == result
    )
    assert not (env.settings.root / "quarantine").exists()
