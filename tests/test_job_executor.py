"""Process tests execute only fixed repository entries or trusted synthetic probes."""

import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
from test_job_control import create, finish
from test_job_control import offline as offline
from test_job_control import setup as setup

from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.guardian import REPOSITORY, clean_environment, prctl
from src.job_control.http import Application
from src.job_control.registry import REGISTRY
from src.job_control.store import Unavailable

PROBE = REPOSITORY / "tests/helpers/job_control_probe.py"


def wait_until(predicate, timeout=8):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if predicate():
            return
        time.sleep(0.02)
    pytest.fail("Bounded process condition not reached")


@pytest.mark.parametrize(
    "mode,reason",
    [
        ("timeout", "timeout"),
        ("cancel", "cancelled"),
        ("exit", None),
        ("orphan_exit", None),
    ],
)
def test_real_nonzero_timeout_cancel_and_descendant_groups(tmp_path, mode, reason):
    # An unrelated direct child is outside the probe's process ancestry/group.
    unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time;time.sleep(30)"], start_new_session=True
    )
    try:
        result = subprocess.run(
            [sys.executable, str(PROBE), mode, str(tmp_path)],
            env=clean_environment(),
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        code, observed, duration = json.loads(
            (tmp_path / "probe-result.json").read_text()
        )
        assert observed == reason and duration < 5
        assert code == (
            7 if mode == "exit" else 0 if mode == "orphan_exit" else -signal.SIGKILL
        )
        if mode != "exit":
            assert all(
                not Path(f"/proc/{pid}").exists()
                for pid in json.loads((tmp_path / "pids.json").read_text())
            )
        assert unrelated.poll() is None
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=3)


def test_actual_resource_limits(tmp_path):
    result = subprocess.run(
        [sys.executable, str(PROBE), "limits", str(tmp_path)],
        env=clean_environment(),
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    limits = json.loads(result.stdout)
    process = REGISTRY["material_planning"]
    for kind, value in (
        (resource.RLIMIT_AS, process.memory_bytes),
        (resource.RLIMIT_CPU, process.cpu_seconds),
        (resource.RLIMIT_FSIZE, process.file_bytes),
        (resource.RLIMIT_NOFILE, process.file_descriptors),
        (resource.RLIMIT_NPROC, process.subprocesses),
        (resource.RLIMIT_CORE, 0),
    ):
        assert limits[str(kind)] == [value, value]


def test_parent_death_cleans_running_root_and_grandchild(tmp_path):
    prctl(36, 1)
    result = subprocess.run(
        [sys.executable, str(PROBE), "crash_parent", str(tmp_path)],
        env=clean_environment(),
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == -signal.SIGKILL, result.stderr
    wait_until(lambda: (tmp_path / "probe-result.json").exists())
    code, reason, duration = json.loads((tmp_path / "probe-result.json").read_text())
    assert code == -signal.SIGKILL and reason == "interrupted" and duration < 5
    assert all(
        not Path(f"/proc/{pid}").exists()
        for pid in json.loads((tmp_path / "pids.json").read_text())
    )
    guardian = json.loads((tmp_path / "guardian.json").read_text())
    os.waitpid(guardian, 0)


def test_worker_singleton_reconciliation_and_no_retry(setup):
    first = Executor(setup.settings)
    try:
        with pytest.raises(BlockingIOError):
            Executor(setup.settings)
        job = create(setup)
        # Crash window after persisted claim, before launching any payload.
        setup.controller.store.transition(
            job.job_id, "running", "dispatching", "Synthetic crash window"
        )
    finally:
        first.close()
    restarted = Executor(setup.settings)
    try:
        assert setup.controller.get(setup.actor, job.job_id).status == "interrupted"
        restarted.step()
        assert not restarted.children
        assert len(setup.controller.store.all()) == 1
    finally:
        restarted.close()


def test_api_restart_during_actual_execution_and_repeated_start(setup):
    executor = Executor(setup.settings)
    try:
        job = create(setup, start=False)
        assert setup.controller.start(setup.actor, job.job_id).status == "queued"
        assert setup.controller.start(setup.actor, job.job_id).job_id == job.job_id
        executor.step()
        setup.controller = Controller(setup.settings)
        result = finish(setup, executor, job)
        assert result.status == "completed" and len(setup.controller.store.all()) == 1
        assert setup.controller.start(setup.actor, job.job_id) == result
        executor.step()
        assert len(setup.controller.store.all()) == 1
    finally:
        executor.close()


def test_cancel_running_adapter_is_confirmed_after_exit(setup):
    executor = Executor(setup.settings)
    try:
        job = create(setup)
        executor.step()
        wait_until(
            lambda: setup.controller.get(setup.actor, job.job_id).started_at is not None
        )
        requested = setup.controller.cancel(setup.actor, job.job_id)
        assert requested.status == "cancel_requested" and requested.finished_at is None
        ended = finish(setup, executor, job)
        assert ended.status == "cancelled" and ended.finished_at is not None
        assert ended.progress is None and not ended.cancellable
    finally:
        executor.close()


def test_input_changed_after_preview_fails_without_overwriting_sources(setup):
    executor = Executor(setup.settings)
    try:
        job = create(setup)
        entry = setup.settings.catalog["demo_snapshots"]
        path = entry.root / entry.roles["manifest"]
        path.write_text("changed after confirmation")
        result = finish(setup, executor, job)
        assert result.status == "failed" and result.exit_code == 2
        assert path.read_text() == "changed after confirmation"
        assert not result.artifact_refs
    finally:
        executor.close()


@pytest.mark.parametrize("revocation", ["identity", "catalog"])
def test_queued_job_rechecks_current_dispatch_authorization(setup, revocation):
    job = create(setup, start=False)
    setup.controller.store.transition(
        job.job_id, "queued", "queued", "Synthetic accepted job before config change"
    )
    settings = setup.settings.model_copy(
        update={"identities": ()} if revocation == "identity" else {"catalog": {}}
    )
    executor = Executor(settings)
    try:
        executor.step()
        assert setup.controller.get(setup.actor, job.job_id).status == "failed"
        assert (
            not executor.children
            and not setup.controller.store.directory(job.job_id).exists()
        )
    finally:
        executor.close()


def test_quality_failure_retains_structured_report(setup):
    entry = setup.settings.catalog["demo_material"]
    path = entry.root / entry.roles["raw"]
    path.write_bytes(b"changed raw; approved bytes contradict normalized hash")
    updated = entry.model_copy(
        update={
            "files": {
                **entry.files,
                entry.roles["raw"]: hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        }
    )
    settings = setup.settings.model_copy(
        update={"catalog": {**setup.settings.catalog, "demo_material": updated}}
    )
    setup.controller = Controller(settings)
    executor = Executor(settings)
    try:
        result = finish(setup, executor, create(setup, process="quality_evaluation"))
        assert (
            result.status == "failed"
            and result.exit_code == 1
            and result.error_class == "input"
        )
        assert result.artifact_refs[0].kind == "quality_report"
    finally:
        executor.close()


def test_parallelism_and_per_process_bound(setup):
    settings = setup.settings.model_copy(update={"max_parallel": 2})
    setup.controller = Controller(settings)
    executor = Executor(settings)
    try:
        first = create(setup)
        second = create(
            setup, key="parallel_second_000000", process="quality_evaluation"
        )
        third = create(setup, key="parallel_third_0000000")
        executor.step()
        assert len(executor.children) == 2
        assert setup.controller.get(setup.actor, third.job_id).status == "queued"
        for job in (first, second, third):
            assert finish(setup, executor, job).status == "completed"
    finally:
        executor.close()


def test_unconfirmed_guardian_loss_quarantines_dispatch(setup):
    executor = Executor(setup.settings)
    try:
        job = create(setup)
        executor.step()
        child = executor.children[job.job_id]
        # SIGKILL before adapter startup: the parent-death chain covers bootstrap.
        child.kill()
        child.wait(timeout=3)
        with pytest.raises(Unavailable, match="quarantined"):
            executor.step()
        assert (setup.settings.root / "quarantine").exists()
        assert not setup.controller.store.worker_available(setup.settings.worker_ttl)
        with pytest.raises(Unavailable):
            create(setup, key="quarantined_request_000")
    finally:
        executor.close()
    with pytest.raises(Unavailable):
        Executor(setup.settings)


def test_real_executor_hard_restart_has_no_duplicate_dispatch(setup):
    prctl(36, 1)  # Adopt/reap only our killed executor's known guardian below.
    config = setup.tmp / "config.json"
    config.write_text(setup.settings.model_dump_json())
    result = subprocess.run(
        [sys.executable, str(PROBE), "crash_executor", str(setup.tmp)],
        env=clean_environment(),
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == -signal.SIGKILL, result.stderr
    details = json.loads((setup.tmp / "crash.json").read_text())
    restarted = Executor(setup.settings)
    try:
        job = setup.controller.get(setup.actor, details["job_id"])
        assert job.status == "interrupted"
        restarted.step()
        assert not restarted.children and len(setup.controller.store.all()) == 1

        def reaped():
            try:
                return os.waitpid(details["guardian"], os.WNOHANG)[0] != 0
            except ChildProcessError:
                return not Path(f"/proc/{details['guardian']}").exists()

        wait_until(reaped)
    finally:
        restarted.close()


def test_real_background_worker_cli_and_api_lifecycle(setup):
    config = setup.tmp / "worker-config.json"
    config.write_text(setup.settings.model_dump_json())
    child = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "scripts.job_control",
            "worker",
            "--config",
            str(config),
        ],
        cwd=REPOSITORY,
        env=clean_environment(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        wait_until(
            lambda: setup.controller.store.worker_available(setup.settings.worker_ttl)
        )
        from test_job_control import request_data

        from scripts.job_control_demo import DEMO_TOKEN

        body = request_data(setup)
        headers = {
            "Authorization": "Bearer " + DEMO_TOKEN,
            "Idempotency-Key": "background_worker_request_0",
        }
        app = Application(setup.controller)
        status, raw, _ = app.request(
            "POST", "/v1/jobs", headers, json.dumps(body).encode()
        )
        assert status == 202
        job_id = json.loads(raw)["job_id"]
        # No in-process Executor.step: the separate CLI worker must do all work.
        app = Application(Controller(setup.settings))

        def ended():
            code, raw, _ = app.request("GET", "/v1/jobs/" + job_id, headers)
            assert code == 200
            return json.loads(raw)["status"] in {"completed", "failed", "interrupted"}

        wait_until(ended)
        assert setup.controller.get(setup.actor, job_id).status == "completed"
        _, raw, _ = app.request("POST", "/v1/jobs", headers, json.dumps(body).encode())
        assert (
            json.loads(raw)["job_id"] == job_id
            and len(setup.controller.store.all()) == 1
        )
        assert app.request("GET", "/v1/jobs/" + job_id + "/logs", headers)[0] == 200
        assert (
            app.request("GET", "/v1/jobs/" + job_id + "/artifacts", headers)[0] == 200
        )
    finally:
        child.terminate()
        child.wait(timeout=8)
