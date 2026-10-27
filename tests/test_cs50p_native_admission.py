"""Synthetic download -> review -> OS admission -> real C16 guardian, offline."""

import json
import os
import subprocess
import sys
import time

import pytest
from test_cs50_batch_worker import offline as offline
from test_cs50_batch_worker import scope as scope
from test_cs50p_mvp import download_args as download_args

from scripts import cs50p_mvp as download_cli
from scripts import cs50p_native as cli
from src.job_control import native_admission as gate
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.models import CatalogEntry, Settings
from src.job_control.store import Store
from src.tools_materials import batch as api


@pytest.fixture
def native(scope, download_args, private_umask):
    report, code = download_cli.download(download_args, transport=scope["transport"])
    assert code == 0 and report["materials"][0]["status"] == "verified"
    limits_value = json.loads(download_args.limits.read_text())
    limits_value["catalog_bytes"] = 128 * 1024**2
    download_args.limits.write_text(json.dumps(limits_value))
    sealed = api.seal(
        scope["batch"],
        download_args.archive,
        scope["tmp"] / "sealed",
        scope["approvals"],
        limits=gate.load_limits(download_args.limits),
    )
    ref, value = next(iter(sealed["catalog"].items()))
    jobs = scope["tmp"] / "native-jobs"
    jobs.mkdir(mode=0o700)
    settings = Settings(
        root=jobs,
        catalog={ref: CatalogEntry.model_validate(value)},
        deployment_gate_required=True,
        deployment_gate_protocol=gate.PROTOCOL,
        native_uid=os.getuid(),
        native_mode="offline-test",
        execution_enabled=True,
        workflows_enabled=True,
        max_queued=1,
        max_parallel=1,
    )
    config = scope["tmp"] / "native-controller.json"
    api.output(config, settings.model_dump(mode="json"))
    gate.initialize(config, download_args.limits)
    return dict(
        settings=settings,
        config=config,
        limits=download_args.limits,
        ref=ref,
        tmp=scope["tmp"],
    )


def approval(n, workflow="native_test", resume=False, ttl=300):
    review = gate.review(n["settings"], n["ref"], workflow, resume=resume)
    return gate.approve(
        n["settings"], n["ref"], workflow, review["review_id"], resume=resume, ttl=ttl
    )


def test_full_download_review_admission_worker_status_processing_result(native):
    grant = approval(native)
    settings = native["settings"]
    assert cli.status(settings, grant["job_id"]).status == "created"
    completed = cli.run(settings, native["limits"], grant["job_id"], offline_test=True)
    assert completed.status == "completed" and completed.exit_code == 0
    value = cli.result(settings, grant["job_id"])
    assert value["report"]["status"] == "completed"
    assert any(
        stage["process_id"] == "material_parsing" and stage["status"] == "completed"
        for stage in value["report"]["stages"]
    )
    assert (settings.root / "native-grants" / (grant["job_id"] + ".used.json")).exists()
    with pytest.raises((PermissionError, FileExistsError)):
        cli.run(settings, native["limits"], grant["job_id"], offline_test=True)
    with pytest.raises(PermissionError):
        approval(native, resume=True)


def test_missing_grant_direct_worker_api_and_store_denied(native):
    settings = native["settings"]
    with pytest.raises((PermissionError, FileNotFoundError)):
        cli.run(settings, native["limits"], "job_missing", offline_test=True)
    with pytest.raises(PermissionError):
        Executor(settings)
    review = gate.review(settings, native["ref"], "native_test")
    with pytest.raises(PermissionError):
        Controller(settings).create(
            gate.actor(settings),
            dict(preview=review["preview"], confirmed=True, start=False),
            "unauthorized_key_1234",
        )
    grant = approval(native)
    with pytest.raises(PermissionError):
        Store(settings.root).transition(
            grant["job_id"], "queued", "queued", "unauthorized"
        )
    with pytest.raises(PermissionError):
        Controller(settings).start(gate.actor(settings), grant["job_id"])


@pytest.mark.parametrize(
    "change",
    [
        "config_bytes",
        "settings",
        "limits",
        "input",
        "owner",
        "expiry",
        "future",
        "foreign_catalog",
    ],
)
def test_changed_or_expired_authority_fails_closed(native, change, monkeypatch):
    grant = approval(native)
    settings = native["settings"]
    if change == "config_bytes":
        native["config"].write_text(native["config"].read_text() + "\n")
    elif change == "settings":
        settings = settings.model_copy(update={"worker_ttl": 2})
    elif change == "limits":
        native["limits"].write_text(native["limits"].read_text() + "\n")
    elif change == "input":
        entry = settings.catalog[native["ref"]]
        (entry.root / "raw.source").write_bytes(b"changed")
    elif change == "owner":
        monkeypatch.setattr(gate.os, "getuid", lambda: os.geteuid() + 1)
    elif change == "expiry":
        monkeypatch.setattr(gate.time, "time", lambda: grant["expires_at"])
    elif change == "future":
        monkeypatch.setattr(gate.time, "time", lambda: grant["approved_at"] - 1)
    elif change == "foreign_catalog":
        settings = settings.model_copy(
            update={"catalog": {"foreign": next(iter(settings.catalog.values()))}}
        )
    with pytest.raises((ValueError, OSError, RuntimeError)):
        cli.run(settings, native["limits"], grant["job_id"], offline_test=True)
    assert (
        cli.status(native["settings"], grant["job_id"]).status == "created"
        if change != "owner"
        else True
    )
    assert not (native["settings"].root / "jobs" / grant["job_id"]).exists()


def test_parallel_approvals_worker_and_replay_claim_blocked(native):
    grant = approval(native)
    with pytest.raises(RuntimeError, match="One active"):
        approval(native, workflow="second_job")
    with gate.lock(native["settings"].root):
        with pytest.raises(BlockingIOError):
            approval(native, workflow="second_job")
    path = native["settings"].root / "native-grants" / (grant["job_id"] + ".used.json")
    gate.write_new(path, dict(crash_after_claim=True))
    with pytest.raises(FileExistsError):
        cli.run(
            native["settings"], native["limits"], grant["job_id"], offline_test=True
        )
    assert cli.cancel(native["settings"], grant["job_id"]).status == "cancelled"
    resumed = approval(native, resume=True)
    assert resumed["job_id"] != grant["job_id"]
    assert resumed["preview"]["parameters"]["previous_run_id"] == grant["job_id"]
    assert (
        cli.run(
            native["settings"], native["limits"], resumed["job_id"], offline_test=True
        ).status
        == "completed"
    )


def test_cancel_without_dispatch_and_new_review_required(native):
    grant = approval(native)
    assert cli.cancel(native["settings"], grant["job_id"]).status == "cancelled"
    with pytest.raises(PermissionError):
        cli.run(
            native["settings"], native["limits"], grant["job_id"], offline_test=True
        )
    old = gate.review(native["settings"], native["ref"], "resume_new")
    with pytest.raises(PermissionError, match="Review changed"):
        gate.approve(
            native["settings"],
            native["ref"],
            "native_test",
            old["review_id"],
            resume=True,
        )


def test_runtime_rejects_synthetic_and_token_identity(native):
    settings = native["settings"]
    with pytest.raises(PermissionError, match="Synthetic"):
        gate.policy(
            settings.model_copy(update={"native_mode": "ssh-runtime"}),
            gate.load_limits(native["limits"]),
        )
    from src.job_control.models import Identity

    with pytest.raises(ValueError):
        Settings.model_validate(
            settings.model_copy(
                update={
                    "identities": (
                        Identity(
                            subject="dummy",
                            role="operator",
                            courses=("cs50_python",),
                            token_sha256="0" * 64,
                        ),
                    )
                }
            ).model_dump(mode="json")
        )


def test_downgrade_and_foreign_gate_rejected(native):
    settings = native["settings"]
    downgraded = settings.model_copy(
        update=dict(
            deployment_gate_protocol="c26-gate-v1",
            deployment_gate_required=False,
            native_uid=None,
            native_mode=None,
        )
    )
    with pytest.raises(PermissionError):
        Executor(downgraded)
    (settings.root / "deployment-gate.v2.jsonl").write_text("{}")
    with pytest.raises(PermissionError):
        gate.review(settings, native["ref"], "native_test")


def test_readonly_preflight_status_do_not_create_jobs(native, capsys):
    before = {
        str(p.relative_to(native["settings"].root)): p.read_bytes()
        for p in native["settings"].root.rglob("*")
        if p.is_file()
    }
    assert (
        cli.main(
            [
                "preflight",
                "--config",
                str(native["config"]),
                "--limits",
                str(native["limits"]),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["mode"] == "offline-test"
    after = {
        str(p.relative_to(native["settings"].root)): p.read_bytes()
        for p in native["settings"].root.rglob("*")
        if p.is_file()
    }
    assert before == after


def test_live_worker_cancel_uses_c16_and_no_second_start(native):
    grant = approval(native)
    cmd = [
        sys.executable,
        "-c",
        "import sys; from types import SimpleNamespace; from src.tools_materials.capacity import shutil; shutil.disk_usage=lambda _:SimpleNamespace(free=100*1024**3); from scripts.cs50p_native import main; raise SystemExit(main(sys.argv[1:]))",
        "run",
        "--offline-test",
        "--config",
        str(native["config"]),
        "--limits",
        str(native["limits"]),
        "--job-id",
        grant["job_id"],
    ]
    child = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    try:
        deadline = time.monotonic() + 20
        while cli.status(native["settings"], grant["job_id"]).status == "created":
            assert child.poll() is None and time.monotonic() < deadline
            time.sleep(0.01)
        cancelled = cli.cancel(native["settings"], grant["job_id"])
        assert cancelled.status in {"cancel_requested", "cancelled"}
        out, err = child.communicate(timeout=20)
        assert child.returncode == 1, (out, err)
        assert cli.status(native["settings"], grant["job_id"]).status == "cancelled"
        with pytest.raises(PermissionError):
            cli.run(
                native["settings"], native["limits"], grant["job_id"], offline_test=True
            )
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)


def test_recover_stopped_claim_requires_fresh_grant(native):
    grant = approval(native)
    path = native["settings"].root / "native-grants" / (grant["job_id"] + ".used.json")
    gate.write_new(path, dict(crash_after_claim=True))
    job = cli.recover(native["settings"], grant["job_id"])
    assert job.status == "cancelled"
    with pytest.raises(PermissionError):
        cli.run(
            native["settings"], native["limits"], grant["job_id"], offline_test=True
        )
    resumed = approval(native, resume=True)
    assert (
        cli.run(
            native["settings"], native["limits"], resumed["job_id"], offline_test=True
        ).status
        == "completed"
    )


def test_recover_live_worker_and_unknown_lifecycle_denied(native):
    import fcntl

    grant = approval(native)
    fd = os.open(native["settings"].root / "worker.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            cli.recover(native["settings"], grant["job_id"])
    finally:
        os.close(fd)
    (native["settings"].root / "jobs" / grant["job_id"]).mkdir(mode=0o700)
    with pytest.raises(FileNotFoundError):
        cli.recover(native["settings"], grant["job_id"])
    assert cli.status(native["settings"], grant["job_id"]).status == "created"


def test_guardian_without_claim_and_result_corruption_denied(native):
    grant = approval(native)
    with pytest.raises(FileNotFoundError):
        gate.child_guard(native["settings"].root, grant["job_id"], os.getppid())
    assert (
        cli.run(
            native["settings"], native["limits"], grant["job_id"], offline_test=True
        ).status
        == "completed"
    )
    value = cli.result(native["settings"], grant["job_id"])
    output = native["settings"].root / value["report"]["output_refs"][0]["path"]
    output.write_bytes(b"changed result")
    with pytest.raises(ValueError, match="integrity"):
        cli.result(native["settings"], grant["job_id"])


def test_exact_cli_review_approve_run_result_and_recover_parser(native, capsys):
    shared = ["--config", str(native["config"]), "--limits", str(native["limits"])]
    scope = ["--source-ref", native["ref"], "--workflow-id", "cli_success"]
    assert cli.main(["review", *shared, *scope]) == 0
    reviewed = json.loads(capsys.readouterr().out)
    assert (
        cli.main(
            [
                "approve",
                *shared,
                *scope,
                "--review-id",
                reviewed["review_id"],
                "--confirm",
            ]
        )
        == 0
    )
    grant = json.loads(capsys.readouterr().out)
    job = ["--job-id", grant["job_id"]]
    assert cli.main(["run", "--offline-test", *shared, *job]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "completed"
    assert cli.main(["result", *shared, *job]) == 0
    assert json.loads(capsys.readouterr().out)["report"]["status"] == "completed"
    assert cli.main(["recover", *shared, *job, "--confirm"]) == 0
    capsys.readouterr()
    assert cli.main(["run", "--offline-test", *shared, *job]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "blocked"


def test_expired_approval_can_cancel_and_malformed_grant_cannot_start(
    native, monkeypatch
):
    grant = approval(native)
    monkeypatch.setattr(gate.time, "time", lambda: grant["expires_at"])
    assert cli.cancel(native["settings"], grant["job_id"]).status == "cancelled"
    monkeypatch.undo()
    fresh = approval(native, resume=True)
    path = native["settings"].root / "native-grants" / (fresh["job_id"] + ".json")
    path.write_text('{"protocol":"c26-native-v1"}')
    with pytest.raises(ValueError):
        cli.run(
            native["settings"], native["limits"], fresh["job_id"], offline_test=True
        )


def test_native_published_schemas_match_models():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    for name, model in [
        ("native_grant.v1.schema.json", gate.Grant),
        ("native_enrollment.v1.schema.json", gate.Enrollment),
    ]:
        assert (
            json.loads((repo / "docs/job_control" / name).read_text())
            == model.model_json_schema()
        )


def test_default_runtime_cli_rejects_offline_grant_before_consumption(native, capsys):
    grant = approval(native)
    with pytest.raises(PermissionError, match="Runtime start rejects"):
        cli.run(native["settings"], native["limits"], grant["job_id"])
    assert (
        cli.main(
            [
                "run",
                "--config",
                str(native["config"]),
                "--limits",
                str(native["limits"]),
                "--job-id",
                grant["job_id"],
            ]
        )
        == 2
    )
    assert json.loads(capsys.readouterr().out)["status"] == "blocked"
    assert not (
        native["settings"].root / "native-grants" / (grant["job_id"] + ".used.json")
    ).exists()
    assert (
        cli.run(
            native["settings"], native["limits"], grant["job_id"], offline_test=True
        ).status
        == "completed"
    )
