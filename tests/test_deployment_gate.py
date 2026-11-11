"""Real C16 SQLite/flock/admission/Executor; synthetic deployment driver only."""

import concurrent.futures
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

import pytest
from test_job_control import create, finish, request_data
from test_job_control import offline as offline
from test_job_control import setup as setup

from src.job_control.controller import Controller
from src.job_control.deployment_gate import (
    JOURNAL,
    LOCK,
    OWNER,
    Approval,
    Blocked,
    Gate,
    Observation,
    Plan,
    _lock,
    _read,
    admission,
    settings_digest,
)
from src.job_control.executor import Executor
from src.job_control.http import Application
from src.job_control.store import Conflict

IMAGE_A = "synthetic.invalid/ui@sha256:" + "a" * 64
IMAGE_B = "synthetic.invalid/ui@sha256:" + "b" * 64


def approval(plan, action="deploy", **updates):
    return Approval(
        **{
            "approval_id": "approval_" + uuid.uuid4().hex,
            "approved_by": "synthetic_operator",
            "action": action,
            "plan_sha256": plan.digest,
            "approved_at": time.time() - 1,
            "expires_at": time.time() + 300,
            "confirmed": True,
            **updates,
        }
    )


class SyntheticDriver:
    """Only replaces a synthetic UI marker; never invokes Docker or a network."""

    def __init__(self, plan):
        self.revision, self.image = plan.current_sha, plan.current_image
        self.calls = []
        self.callback = None
        self.bad = {}
        self.permit = None
        self.container_id = "synthetic_initial_container"

    def observe(self, plan):
        return Observation(
            **{
                "resource_id": plan.resource_id,
                "revision": self.revision,
                "image": self.image,
                "container_id": self.container_id,
                "observed_at": time.time(),
                "healthy": True,
                "ready": True,
                "triggers_disabled": True,
                "single_resource_change": True,
                "gate_protocol": "c26-gate-v1",
                "external_jobs_idle": True,
                "external_intake_fenced": True,
                "settings_sha256": plan.settings_sha256,
                "persistence_sha256": plan.persistence_sha256,
                "protected_resources_sha256": plan.protected_resources_sha256,
                **self.bad,
            }
        )

    def deploy(self, plan, permit):
        permit.check()
        self.calls.append(plan.target_sha)
        self.permit = permit
        if self.callback:
            self.callback()
        self.revision, self.image = plan.target_sha, plan.target_image
        self.container_id = "synthetic_replacement_" + uuid.uuid4().hex


@pytest.fixture
def gated(setup):
    settings = setup.settings.model_copy(
        update={"deployment_gate_required": True, "worker_ttl": 30}
    )
    setup.settings = settings
    setup.controller = Controller(settings)
    setup.app = Application(setup.controller)
    gate = Gate(settings)
    gate.initialize()
    worker = Executor(settings)
    plan = Plan(
        resource_id="existing_ui",
        role="ui",
        current_sha="a" * 40,
        current_image=IMAGE_A,
        target_sha="b" * 40,
        target_image=IMAGE_B,
        settings_sha256=settings_digest(settings),
        persistence_sha256="c" * 64,
        protected_resources_sha256="d" * 64,
    )
    driver = SyntheticDriver(plan)
    initial = plan.model_copy(
        update={"target_sha": plan.current_sha, "target_image": plan.current_image}
    )
    gate.release(initial, approval(initial, "resume"), driver)
    setup.gate, setup.worker, setup.plan, setup.driver = gate, worker, plan, driver
    try:
        yield setup
    finally:
        setup.worker.close()


@pytest.mark.parametrize(
    "change",
    [
        None,
        {"confirmed": False},
        {"expires_at": 1.0},
        {"plan_sha256": "f" * 64},
        {"approved_at": time.time() + 1000},
        {"action": "resume"},
    ],
)
def test_no_exact_current_approval_no_deployment(gated, change):
    release = approval(gated.plan, **change) if change is not None else None
    with pytest.raises(Blocked):
        gated.gate.run(gated.plan, release, gated.driver, drain_timeout=0)
    assert not gated.driver.calls
    assert gated.gate.status()["phase"] == "open"
    assert _read(gated.settings.root)[-1]["reason"] == "deployment_request_refused"


def test_active_real_job_prevents_change_and_finishes_without_cancel(gated):
    job = create(gated)
    gated.worker.step()
    assert gated.controller.get(gated.actor, job.job_id).status == "running"
    with pytest.raises(Blocked, match="drain_timeout"):
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver, drain_timeout=0)
    assert not gated.driver.calls
    assert gated.gate.status()["phase"] == "recovery"
    result = finish(gated, gated.worker, job)
    assert result.status == "completed"
    assert result.artifact_refs


def test_push_does_not_supply_operator_authority(gated):
    job = create(gated)
    with pytest.raises(Blocked):
        gated.gate.run(gated.plan, None, gated.driver)
    assert not gated.driver.calls
    assert gated.controller.get(gated.actor, job.job_id).status == "queued"


def wait_phase(gate, phase):
    until = time.monotonic() + 5
    while time.monotonic() < until:
        if gate.status().get("phase") == phase:
            return
        time.sleep(0.01)
    pytest.fail("bounded gate phase not reached")


def test_drain_runs_previously_accepted_queue_and_refuses_new_jobs(gated):
    jobs = [create(gated, key="synthetic_request_key_" + str(i)) for i in range(2)]
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(
            gated.gate.run,
            gated.plan,
            approval(gated.plan),
            gated.driver,
            drain_timeout=20,
        )
        wait_phase(gated.gate, "draining")
        with pytest.raises(Blocked):
            create(gated, key="new_request_during_drain")
        for job in jobs:
            assert finish(gated, gated.worker, job).status == "completed"
        assert future.result(timeout=10)["status"] == "verified"
    assert gated.gate.status()["phase"] == "verified"
    assert len(gated.driver.calls) == 1
    with pytest.raises(Blocked):
        create(gated, key="new_request_after_deploy")


def test_start_and_direct_store_queue_release_are_fenced(gated):
    job = create(gated, start=False)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(
            gated.gate.run,
            gated.plan,
            approval(gated.plan),
            gated.driver,
            drain_timeout=0.5,
        )
        wait_phase(gated.gate, "draining")
        for start in (
            lambda: gated.controller.start(gated.actor, job.job_id),
            lambda: gated.controller.store.transition(
                job.job_id, "queued", "queued", "test"
            ),
        ):
            with pytest.raises(Blocked):
                start()
        with pytest.raises(Blocked):
            future.result(timeout=3)
    assert gated.controller.get(gated.actor, job.job_id).status == "created"
    assert not gated.driver.calls


def test_real_submission_after_idle_in_another_process_is_rejected(gated):
    config = gated.tmp / "config.json"
    config.write_text(gated.settings.model_dump_json())
    request = gated.tmp / "request.json"
    request.write_text(json.dumps(request_data(gated)))
    code = """
import json,sys
from src.job_control.controller import Controller
from src.job_control.models import load_settings
from src.job_control.store import Unavailable
from scripts.job_control_demo import DEMO_TOKEN
c=Controller(load_settings(sys.argv[1]))
try:
 c.create(c.authenticate('Bearer '+DEMO_TOKEN),json.load(open(sys.argv[2])),'concurrent_submit_after_idle')
except Unavailable:
 print('refused')
else:
 raise SystemExit(3)
"""

    def submit():
        result = subprocess.run(
            [sys.executable, "-c", code, str(config), str(request)],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0 and result.stdout.strip() == "refused", (
            result.stderr
        )

    gated.driver.callback = submit
    gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    assert gated.controller.store.all() == ()


def test_inflight_preview_cannot_commit_after_gate_idle(gated, monkeypatch):
    import src.job_control.controller as module

    value = request_data(gated)
    reached, release = threading.Event(), threading.Event()
    original = module.resolve_preview

    def delayed(*args, **kwargs):
        result = original(*args, **kwargs)
        reached.set()
        assert release.wait(10)
        return result

    monkeypatch.setattr(module, "resolve_preview", delayed)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        submitted = pool.submit(
            gated.controller.create, gated.actor, value, "inflight_confirmed_request"
        )
        assert reached.wait(5)

        def cross_boundary():
            release.set()
            with pytest.raises(Blocked):
                submitted.result(timeout=5)

        gated.driver.callback = cross_boundary
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    assert not gated.controller.store.all()


@pytest.mark.parametrize(
    "unknown", ["heartbeat", "missing_worker", "schema", "quarantine"]
)
def test_unknown_worker_or_queue_is_blocked(gated, unknown):
    if unknown == "heartbeat":
        gated.controller.store.heartbeat(0)
    elif unknown == "missing_worker":
        os.close(gated.worker.deployment_lease)
        gated.worker.deployment_lease = None
    elif unknown == "schema":
        with gated.controller.store.connection(write=True) as db:
            db.execute("PRAGMA user_version=2")
    else:
        (gated.settings.root / "quarantine").write_text("synthetic\n")
    with pytest.raises((Blocked, ValueError)):
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver, drain_timeout=0)
    assert not gated.driver.calls
    assert gated.gate.status()["phase"] == "recovery"


@pytest.mark.parametrize(
    "field,value",
    [
        ("healthy", False),
        ("ready", False),
        ("revision", "c" * 40),
        ("image", IMAGE_A),
        ("persistence_sha256", "e" * 64),
        ("protected_resources_sha256", "e" * 64),
    ],
)
def test_bad_postdeploy_health_version_or_scope_stays_closed(gated, field, value):
    def fail_after_change():
        gated.driver.bad[field] = value

    gated.driver.callback = fail_after_change
    with pytest.raises(Blocked):
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    assert gated.gate.status()["phase"] == "recovery"
    with pytest.raises(Blocked):
        create(gated)


def test_success_requires_separate_fresh_resume_approval(gated):
    deploy = approval(gated.plan)
    gated.gate.run(gated.plan, deploy, gated.driver)
    with pytest.raises(Blocked):
        gated.gate.release(gated.plan, deploy, gated.driver)
    with pytest.raises(Blocked):
        gated.driver.permit.check()
    gated.gate.release(gated.plan, approval(gated.plan, "resume"), gated.driver)
    assert gated.gate.status()["phase"] == "open"
    assert create(gated).status == "queued"


def test_explicit_recovery_then_separate_resume(gated):
    gated.driver.callback = lambda: gated.driver.bad.update(healthy=False)
    with pytest.raises(Blocked):
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    gated.driver.bad = {}
    with pytest.raises(Blocked):
        gated.gate.release(gated.plan, approval(gated.plan, "resume"), gated.driver)
    gated.gate.release(
        gated.plan, approval(gated.plan, "recover"), gated.driver, recovery=True
    )
    assert gated.gate.status()["phase"] == "verified"
    gated.gate.release(gated.plan, approval(gated.plan, "resume"), gated.driver)
    assert gated.gate.status()["phase"] == "open"


def test_owner_lock_blocks_second_coordinator(gated):
    with _lock(gated.settings.root, OWNER), pytest.raises(Blocked):
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    assert not gated.driver.calls


def test_torn_journal_and_missing_required_gate_fail_closed_without_cancelling(gated):
    job = create(gated)
    gated.worker.step()
    path = gated.settings.root / JOURNAL
    with path.open("ab") as stream:
        stream.write(b'{"torn":')
    assert gated.gate.status()["phase"] == "unknown"
    with pytest.raises(Blocked):
        create(gated, key="new_request_torn_gate")
    assert finish(gated, gated.worker, job).status == "completed"
    path.unlink()
    with pytest.raises(Blocked):
        create(gated, key="new_request_missing_gate")


def test_journal_records_approval_and_does_not_change_pilot_or_db_schema(gated):
    pilot = gated.tmp / "separate_week0_pilot"
    pilot.mkdir()
    original = {
        "raw": b"synthetic raw",
        "receipt": b"synthetic receipt",
        "jobs.sqlite3": b"untouched independent pilot",
    }
    for name, data in original.items():
        (pilot / name).write_bytes(data)
    with gated.controller.store.connection() as db:
        before = list(db.execute("SELECT sql FROM sqlite_master ORDER BY name"))
    gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    rows = _read(gated.settings.root)
    assert {r["phase"] for r in rows} >= {
        "held",
        "open",
        "draining",
        "deploying",
        "verifying",
        "verified",
    }
    assert rows[-1]["approval"]["approved_by"] == "synthetic_operator"
    assert all((pilot / name).read_bytes() == data for name, data in original.items())
    with gated.controller.store.connection() as db:
        assert list(db.execute("SELECT sql FROM sqlite_master ORDER BY name")) == before


def test_existing_conflict_contract_survives_admission_guard(gated):
    with pytest.raises(Conflict, match="fixed conflict"):
        with admission(gated.settings):
            raise Conflict("fixed conflict")


@pytest.mark.parametrize(
    "bad",
    [
        {"triggers_disabled": False},
        {"single_resource_change": False},
        {"external_jobs_idle": False},
        {"external_intake_fenced": False},
        {"observed_at": 1.0},
        {"resource_id": "wrong_resource"},
        {"settings_sha256": "e" * 64},
    ],
)
def test_uncontrolled_trigger_or_uncovered_external_job_prevents_deployment(gated, bad):
    gated.driver.bad = bad
    with pytest.raises(Blocked):
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    assert not gated.driver.calls
    assert gated.gate.status()["phase"] == "open"


def test_terminal_row_does_not_hide_guardian_lifecycle_lock(gated):
    job = create(gated)
    gated.worker.step()
    assert finish(gated, gated.worker, job).status == "completed"
    path = gated.controller.store.directory(job.job_id)
    with _lock(path, "execution.lock"), pytest.raises(Blocked, match="drain_timeout"):
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver, drain_timeout=0)
    assert not gated.driver.calls


def test_coordinator_process_crash_retains_fence_and_needs_explicit_recovery(gated):
    import multiprocessing

    def coordinator():
        gated.driver.callback = lambda: os._exit(17)
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver)

    child = multiprocessing.get_context("fork").Process(target=coordinator)
    child.start()
    child.join(10)
    assert child.exitcode == 17
    assert gated.gate.status()["phase"] == "deploying"
    with pytest.raises(Blocked):
        create(gated)
    # The synthetic deploy callback crashed before changing its resource.
    actual = gated.plan.model_copy(
        update={
            "target_sha": gated.plan.current_sha,
            "target_image": gated.plan.current_image,
        }
    )
    gated.gate.release(actual, approval(actual, "recover"), gated.driver, recovery=True)
    assert gated.gate.status()["phase"] == "verified"
    gated.gate.release(actual, approval(actual, "resume"), gated.driver)
    assert gated.gate.status()["phase"] == "open"


def test_replacement_worker_starts_paused_on_same_queue_without_overlap(gated):
    gated.plan = gated.plan.model_copy(
        update={"resource_id": "existing_worker", "role": "worker"}
    )
    original_db = gated.controller.store.path.stat().st_ino

    def replace_only_after_idle():
        gated.worker.close()
        gated.worker = Executor(gated.settings)
        gated.worker.step()
        assert gated.gate.status()["phase"] == "deploying"
        assert gated.worker.children == {}

    gated.driver.callback = replace_only_after_idle
    gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    assert gated.controller.store.path.stat().st_ino == original_db
    assert gated.gate.status()["phase"] == "verified"


def test_same_container_claiming_new_version_is_not_a_verified_replacement(gated):
    class NoReplacement(SyntheticDriver):
        def deploy(self, plan, permit):
            permit.check()
            self.revision, self.image = plan.target_sha, plan.target_image

    with pytest.raises(Blocked, match="replacement_instance"):
        gated.gate.run(gated.plan, approval(gated.plan), NoReplacement(gated.plan))
    assert gated.gate.status()["phase"] == "recovery"


def test_status_is_read_only_and_reinitialize_cannot_reopen_missing_lock(gated):
    root = gated.settings.root
    path = root / JOURNAL
    before = path.read_bytes(), path.stat().st_mtime_ns
    assert gated.gate.status()["phase"] == "open"
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    (root / LOCK).unlink()
    with pytest.raises(Blocked):
        gated.gate.initialize()
    assert not (root / LOCK).exists()
    assert gated.gate.status()["phase"] == "unknown"


@pytest.mark.parametrize("damage", ["hash", "permissions", "symlink", "hardlink"])
def test_invalid_or_unsafe_journal_fails_closed(gated, damage):
    root = gated.settings.root
    path = root / JOURNAL
    if damage == "hash":
        body = path.read_bytes().replace(b'"open"', b'"held"')
        path.write_bytes(body)
    elif damage == "permissions":
        path.chmod(0o644)
    elif damage == "symlink":
        target = gated.tmp / "journal-target"
        path.rename(target)
        path.symlink_to(target)
    else:
        os.link(path, gated.tmp / "journal-hardlink")
    assert gated.gate.status()["status"] == "blocked"
    with pytest.raises(Blocked):
        create(gated)


def test_isolated_restore_preserves_journal_but_holds_admissions(gated):
    from src.job_control.deployment_gate import hold_restored_root
    from src.job_control.operations import copy_files

    target = gated.tmp / "isolated_restore"
    copy_files(gated.settings.root, target, workspace=True)
    old = (gated.settings.root / JOURNAL).read_bytes()
    hold_restored_root(target)
    assert (target / JOURNAL).read_bytes().startswith(old)
    assert _read(target)[-1]["phase"] == "held"
    assert (gated.settings.root / JOURNAL).read_bytes() == old


def test_cli_never_exports_a_permit_or_calls_a_deployment(gated, capsys):
    from scripts.deployment_gate import main

    config = gated.tmp / "controller.json"
    config.write_text(gated.settings.model_dump_json())
    config.chmod(0o600)
    plan_path = gated.tmp / "plan.json"
    plan_path.write_text(gated.plan.model_dump_json())
    plan_path.chmod(0o600)
    approval_path = gated.tmp / "approval.json"
    approval_path.write_text(approval(gated.plan).model_dump_json())
    approval_path.chmod(0o600)
    assert (
        main(
            [
                "check-plan",
                "--config",
                str(config),
                "--plan",
                str(plan_path),
                "--approval",
                str(approval_path),
                "--action",
                "deploy",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result == {
        "status": "plan_valid_only",
        "deployment_permitted": False,
        "production_release": "blocked",
    }
    assert not gated.driver.calls


def test_unhealthy_known_ui_can_rollback_with_new_exact_approval(gated):
    gated.driver.callback = lambda: gated.driver.bad.update(healthy=False, ready=False)
    with pytest.raises(Blocked):
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    rollback = gated.plan.model_copy(
        update={
            "current_sha": gated.plan.target_sha,
            "current_image": gated.plan.target_image,
            "target_sha": gated.plan.current_sha,
            "target_image": gated.plan.current_image,
        }
    )
    gated.driver.callback = lambda: gated.driver.bad.clear()
    gated.gate.run(rollback, approval(rollback, "rollback"), gated.driver)
    assert gated.gate.status()["phase"] == "verified"
    assert gated.driver.revision == gated.plan.current_sha
    with pytest.raises(Blocked):
        create(gated)
    gated.gate.release(rollback, approval(rollback, "resume"), gated.driver)
    assert gated.gate.status()["phase"] == "open"


@pytest.mark.parametrize("stage", ["observe", "deploy"])
def test_driver_exceptions_are_sanitized_and_audited(gated, stage):
    def fail(*args):
        raise RuntimeError("synthetic_private_transport_details")

    setattr(gated.driver, stage, fail)
    with pytest.raises(Blocked) as caught:
        gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    assert "synthetic_private_transport_details" not in str(caught.value)
    assert (
        b"synthetic_private_transport_details"
        not in (gated.settings.root / JOURNAL).read_bytes()
    )
    assert gated.gate.status()["phase"] == (
        "open" if stage == "observe" else "recovery"
    )


def test_actual_authenticated_http_submission_is_unavailable_during_fence(gated):
    from scripts.job_control_demo import DEMO_TOKEN

    gated.gate.run(gated.plan, approval(gated.plan), gated.driver, drain_timeout=0)
    headers = {
        "Authorization": "Bearer " + DEMO_TOKEN,
        "Idempotency-Key": "http_during_deployment_fence",
    }
    status, body, _ = gated.app.request(
        "POST", "/v1/jobs", headers, json.dumps(request_data(gated)).encode()
    )
    assert status == 503
    assert json.loads(body)["error"]["code"] == "unavailable"
    assert gated.app.request("GET", "/v1/jobs", headers)[0] == 200
    assert gated.app.request("POST", "/v1/jobs", {}, b"{}")[0] == 401
    assert gated.controller.store.all() == ()


@pytest.mark.parametrize(
    "data",
    [
        b"[]\n",
        b"null\n",
        b'"invalid"\n',
        b'{"sha256":0}\n',
        b"[" * 2500 + b"0" + b"]" * 2500 + b"\n",
    ],
)
def test_valid_json_with_invalid_journal_shape_is_blocked(gated, data):
    (gated.settings.root / JOURNAL).write_bytes(data)
    assert gated.gate.status()["phase"] == "unknown"
    with pytest.raises(Blocked):
        create(gated)


def test_full_c22_backup_restore_of_gated_queue_is_inactive(gated):
    from src.job_control.operations import backup, restore

    config = gated.tmp / "backup-controller.json"
    config.write_text(gated.settings.model_dump_json())
    config.chmod(0o600)
    snapshot, restored = gated.tmp / "snapshot", gated.tmp / "restored"
    before = (gated.settings.root / JOURNAL).read_bytes()
    gated.worker.close()
    try:
        backup(config, snapshot)
        result = restore(snapshot, restored)
        assert result["activated"] is False
        assert (restored / JOURNAL).read_bytes().startswith(before)
        restored_settings = gated.settings.model_copy(update={"root": restored})
        assert Gate(restored_settings).status()["phase"] == "held"
        with pytest.raises(Blocked):
            with admission(restored_settings):
                pytest.fail("restored queue was activated")
        assert (gated.settings.root / JOURNAL).read_bytes() == before
    finally:
        gated.worker = Executor(gated.settings)


@pytest.mark.parametrize(
    "image",
    [
        "synthetic.invalid/ui:latest",
        "https://synthetic.invalid/ui@sha256:" + "a" * 64,
        "user:private@synthetic.invalid/ui@sha256:" + "a" * 64,
    ],
)
def test_image_plans_reject_mutable_tags_urls_and_embedded_credentials(gated, image):
    with pytest.raises(ValueError):
        Plan.model_validate({**gated.plan.model_dump(), "target_image": image})


def test_short_diagnostic_lock_does_not_abort_coordinator(gated):
    with concurrent.futures.ThreadPoolExecutor() as pool:
        with _lock(gated.settings.root, LOCK):
            future = pool.submit(
                gated.gate.run, gated.plan, approval(gated.plan), gated.driver
            )
            time.sleep(0.1)
        assert future.result(timeout=5)["status"] == "verified"
    assert len(gated.driver.calls) == 1


def test_resume_approval_expiring_during_live_probe_cannot_reopen(gated):
    gated.gate.run(gated.plan, approval(gated.plan), gated.driver)
    expiring = approval(gated.plan, "resume", expires_at=time.time() + 0.15)
    observe = gated.driver.observe

    def slow_probe(plan):
        time.sleep(0.2)
        return observe(plan)

    gated.driver.observe = slow_probe
    with pytest.raises(Blocked, match="approval_missing_expired"):
        gated.gate.release(gated.plan, expiring, gated.driver)
    assert gated.gate.status()["phase"] == "verified"


def test_deploy_approval_expiring_during_probe_never_starts_drain(gated):
    expiring = approval(gated.plan, expires_at=time.time() + 0.15)
    observe = gated.driver.observe

    def slow_probe(plan):
        time.sleep(0.2)
        return observe(plan)

    gated.driver.observe = slow_probe
    with pytest.raises(Blocked, match="approval_missing_expired"):
        gated.gate.run(gated.plan, expiring, gated.driver)
    assert not gated.driver.calls
    assert gated.gate.status()["phase"] == "open"


@pytest.mark.parametrize("role", [Controller, Executor])
@pytest.mark.parametrize("directory_exists", [False, True])
def test_required_gate_never_creates_replacement_queue_on_missing_mount(
    tmp_path, role, directory_exists
):
    from src.job_control.models import Settings

    root = tmp_path / "missing_queue"
    if directory_exists:
        root.mkdir(mode=0o700)
    settings = Settings(
        root=root, execution_enabled=True, deployment_gate_required=True
    )
    with pytest.raises(Blocked, match="existing_private_c16_queue_required"):
        role(settings)
    assert root.exists() == directory_exists
    if directory_exists:
        assert list(root.iterdir()) == []
