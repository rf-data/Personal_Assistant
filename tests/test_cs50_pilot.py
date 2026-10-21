"""Synthetic source bundles, grants and receipts; no real HTTP or host mounts."""

import fcntl
import json
import os
import socket
import sqlite3
import time
from types import SimpleNamespace

import httpx
import pytest

from scripts import cs50_pilot as pilot
from scripts.cs50_workflow_demo import inputs as demo_inputs
from src import runtime_paths
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.models import TERMINAL, Identity, Settings
from src.tools_materials import batch as api


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("Unapproved real network access")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def environment(tmp_path, monkeypatch):
    os.umask(0o077)
    code = tmp_path / "app"
    code.mkdir(mode=0o700)
    mounts = tuple(code / name for name in ("data", "logs", ".cache", "configuration"))
    for path in mounts:
        path.mkdir(mode=0o700)
    (code / "scripts").mkdir(mode=0o700)
    for name in pilot.SCRIPTS:
        (code / "scripts" / name).write_text("# synthetic presence marker\n")
    identities = {
        path: dict(
            device="8:1",
            root="/srv/synthetic/" + path.name,
            filesystem="ext4",
            source="/dev/vda1",
            writable=True,
        )
        for path in mounts
    }
    monkeypatch.setattr(pilot, "CODE", code)
    monkeypatch.setattr(pilot, "MOUNTS", mounts)
    monkeypatch.setattr(runtime_paths, "__file__", str(code / "src/runtime_paths.py"))
    monkeypatch.setattr(runtime_paths, "mounts", lambda: dict(identities))
    # The host has <5 GiB free. Model capacity, never weaken production limits.
    monkeypatch.setattr(
        pilot.shutil, "disk_usage", lambda _p: SimpleNamespace(free=100 * 1024**3)
    )
    snapshots = tmp_path / "synthetic-discovery"
    demo_inputs(snapshots)
    (snapshots / "cs50_python/week0.html").rename(snapshots / "cs50_python/week_0.html")
    manifest = json.loads((snapshots / "manifest.json").read_text())
    for page in manifest["courses"][0]["pages"]:
        page["file"] = page["file"].replace("week0.html", "week_0.html")
    (snapshots / "manifest.json").write_text(json.dumps(manifest))
    hashes = {p["file"]: p["sha256"] for p in manifest["courses"][0]["pages"]}
    monkeypatch.setattr(pilot, "SNAPSHOTS", hashes)
    plan = api.plan
    monkeypatch.setattr(
        api, "plan", lambda m, c, r, **_k: plan(m, c, r, synthetic=True)
    )
    bundle = tmp_path / "bundle"
    pilot.export(snapshots, bundle)
    root = mounts[0] / "synthetic-pilot"
    policy = mounts[3] / "synthetic.paths.json"
    pilot.authorize_paths(root, policy)
    monkeypatch.setenv(runtime_paths.POLICY_ENV, str(policy))
    token = mounts[3] / "synthetic.token"
    token.write_text("synthetic-token-only-for-isolated-tests-1234567890\n")
    token.chmod(0o600)
    return SimpleNamespace(
        root=root,
        bundle=bundle,
        policy=policy,
        token=token,
        mounts=mounts,
        identities=identities,
        snapshots=snapshots,
    )


def initialize(env):
    return pilot.initialize(
        env.bundle, env.root, "synthetic-review-operator", env.token
    )


def approve(env):
    path = env.root / "approvals.json"
    document = json.loads(path.read_text())
    grant = document["sources"][0]
    for name in grant:
        if name.endswith("_reference"):
            grant[name] = "synthetic-test-operator-decision"
    grant.update(download=True, process=True)
    path.write_text(json.dumps(document))
    return api.load_approvals(path)


def planned(env):
    batch = pilot.selected(env.root / "inputs/manifest.json")
    api.output(
        env.root / "batch.json",
        {
            "batch": batch.model_dump(mode="json"),
            "sha256": api.fingerprint(batch.model_dump(mode="json")),
        },
    )
    return batch


def sealed(env):
    approvals = approve(env)
    batch = planned(env)
    calls = []

    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            content=b"<html><main><h1>Synthetic pilot</h1><p>One local test source.</p></main></html>",
        )

    report = api.obtain(
        batch,
        env.root / "archive",
        approvals,
        execute=True,
        transport=httpx.MockTransport(respond),
        limits=pilot.limits(),
    )
    assert report["materials"][0]["status"] == "verified" and calls == [pilot.URL]
    result = api.seal(
        batch,
        env.root / "archive",
        env.root / "catalog",
        approvals,
        limits=pilot.limits(),
    )
    assert len(result["catalog"]) == 1
    return batch


def snapshot(root):
    return {
        str(p.relative_to(root)): (p.stat().st_mode, p.read_bytes())
        for p in root.rglob("*")
        if p.is_file()
    }


def test_bundle_and_incomplete_approval_are_not_execution_permission(environment):
    env = environment
    assert initialize(env)["status"] == "awaiting_operator_approval"
    before = snapshot(env.root)
    with pytest.raises(pilot.Blocked, match="approval_missing"):
        pilot.preflight(env.root, "plan")
    assert snapshot(env.root) == before
    assert not (env.root / "jobs/jobs.sqlite3").exists()
    assert not (env.root / "archive/.materials.lock").exists()


def test_source_to_sealed_catalog_to_real_controller_configuration(environment):
    env = environment
    initialize(env)
    approve(env)
    assert pilot.preflight(env.root, "plan")["status"] == "ready"
    batch = sealed(env)
    result = pilot.configure(env.root)
    before = snapshot(env.root)
    assert pilot.preflight(env.root, "process")["status"] == "ready"
    assert snapshot(env.root) == before
    config = json.loads((env.root / "controller.json").read_text())
    assert config["max_parallel"] == config["max_queued"] == 1
    assert config["max_jobs"] == 3 and len(config["catalog"]) == 1
    assert result["source_ref"] in config["catalog"]
    assert batch.source_origin == "synthetic"
    with pytest.raises(FileExistsError):
        pilot.configure(env.root)


def test_unauthorized_step_blocks_download_preflight(environment):
    env = environment
    initialize(env)
    approve(env)
    planned(env)
    document = json.loads((env.root / "approvals.json").read_text())
    document["sources"][0]["process"] = False
    (env.root / "approvals.json").write_text(json.dumps(document))
    with pytest.raises(pilot.Blocked, match="approval_missing"):
        pilot.preflight(env.root, "download")


@pytest.mark.parametrize(
    "problem",
    [
        "identity",
        "token",
        "limits",
        "script",
        "space",
        "mount",
        "mount_identity",
        "quarantine",
        "unknown_job_data",
    ],
)
def test_clear_readiness_blockers_do_not_mutate_inputs(
    environment, monkeypatch, problem
):
    env = environment
    initialize(env)
    approve(env)
    if problem == "identity":
        identity = Identity(
            subject="synthetic-viewer",
            role="viewer",
            courses=(pilot.COURSE,),
            token_sha256=api.sha(env.token.read_text().strip().encode()),
        )
        (env.root / "identity.json").write_text(identity.model_dump_json())
    elif problem == "token":
        (env.root / "operator.token").write_text("changed")
    elif problem == "limits":
        document = json.loads((env.root / "limits.json").read_text())
        document["max_materials"] = 2
        (env.root / "limits.json").write_text(json.dumps(document))
    elif problem == "script":
        (pilot.CODE / "scripts/cs50_worker.py").unlink()
    elif problem == "space":
        monkeypatch.setattr(
            pilot.shutil,
            "disk_usage",
            lambda _p: SimpleNamespace(free=pilot.RESERVE - 1),
        )
    elif problem == "mount":
        del env.identities[env.mounts[0]]
    elif problem == "mount_identity":
        env.identities[env.mounts[0]] = dict(
            env.identities[env.mounts[0]], device="8:2"
        )
    elif problem == "quarantine":
        (env.root / "jobs/quarantine").write_text("synthetic-only")
    else:
        (env.root / "jobs/foreign").write_text("synthetic-only")
    before = snapshot(env.root)
    with pytest.raises((ValueError, OSError)):
        pilot.preflight(env.root, "plan")
    assert snapshot(env.root) == before


def test_active_lock_is_not_stolen_or_created(environment):
    env = environment
    initialize(env)
    approve(env)
    lock = env.root / "jobs/worker.lock"
    lock.touch(mode=0o600)
    with lock.open("rb") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = snapshot(env.root)
        with pytest.raises(pilot.Blocked, match="active"):
            pilot.preflight(env.root, "plan")
        assert snapshot(env.root) == before


def test_raw_receipt_and_catalog_tampering_rejected(environment):
    env = environment
    initialize(env)
    batch = sealed(env)
    pilot.configure(env.root)
    downloader = pilot.MaterialDownloader(env.root / "archive")
    raw, receipt = downloader.paths(api.reviewed(batch.materials[0]))
    old = raw.read_bytes()
    raw.write_bytes(b"tampered synthetic bytes")
    with pytest.raises(ValueError):
        pilot.preflight(env.root, "process")
    raw.write_bytes(old)
    receipt.write_text("{}")
    with pytest.raises(ValueError):
        pilot.preflight(env.root, "process")


def test_no_overwrite_no_adoption_no_loviscach_access(environment):
    env = environment
    protected = env.mounts[0] / "lectures/loviscach"
    protected.mkdir(parents=True)
    (protected / "keep").write_text("synthetic-protected-bytes")
    before = snapshot(protected)
    with pytest.raises(pilot.Blocked):
        pilot.authorize_paths(protected, env.mounts[3] / "wrong.paths.json")
    initialize(env)
    with pytest.raises(pilot.Blocked, match="exists"):
        initialize(env)
    with pytest.raises(pilot.Blocked, match="exists"):
        pilot.export(env.snapshots, env.bundle)
    assert snapshot(protected) == before


def test_corrupt_bundle_never_creates_destination(environment):
    env = environment
    (env.bundle / "cs50_python/week_0.html").write_text("changed synthetic snapshot")
    with pytest.raises(pilot.Blocked, match="hash"):
        initialize(env)
    assert not env.root.exists()


def test_cli_rejection_does_not_print_private_path_or_token(environment, capsys):
    env = environment
    assert pilot.main(["preflight", "--root", str(env.root), "--phase", "plan"]) == 2
    output = capsys.readouterr().out
    assert json.loads(output)["status"] == "blocked"
    assert str(env.root) not in output and env.token.read_text().strip() not in output


def test_generated_configuration_runs_one_real_synthetic_workflow(environment):
    env = environment
    initialize(env)
    batch = sealed(env)
    pilot.configure(env.root)
    assert pilot.preflight(env.root, "process")["status"] == "ready"
    settings = Settings.model_validate_json((env.root / "controller.json").read_bytes())
    controller = Controller(settings)
    actor = controller.authenticate("Bearer " + env.token.read_text().strip())
    worker = Executor(settings)
    try:
        document = json.loads((env.root / "catalog/catalog.json").read_text())
        ref = next(iter(document["catalog"]))
        result = api.control(
            env.root / "controller.json",
            env.root / "operator.token",
            env.root / "catalog/catalog.json",
            "execute",
            [ref],
            confirm=True,
            limits=pilot.limits(),
        )
        job_id = result["workflows"][0]["job"]["job_id"]
        until = time.monotonic() + 60
        while controller.get(actor, job_id).status not in TERMINAL:
            assert time.monotonic() < until, "Synthetic workflow timed out"
            worker.step()
            time.sleep(0.05)
        assert controller.get(actor, job_id).status == "completed"
        again = api.control(
            env.root / "controller.json",
            env.root / "operator.token",
            env.root / "catalog/catalog.json",
            "resume",
            [ref],
            confirm=True,
            limits=pilot.limits(),
        )
        assert len(controller.store.all()) == 1
        report = again["workflows"][0]["report"]
        assert report["status"] == "completed"
        assert len(report["stages"]) == 5
        for artifact in report["output_refs"]:
            data = (settings.root / artifact["path"]).read_bytes()
            assert (
                api.sha(data) == artifact["sha256"]
                and len(data) == artifact["size_bytes"]
            )
        assert batch.source_origin == "synthetic"
    finally:
        worker.close()
    before = snapshot(env.root)
    assert pilot.preflight(env.root, "process")["status"] == "ready"
    assert snapshot(env.root) == before


def test_non_http_receipt_cannot_pass_readiness(environment):
    env = environment
    initialize(env)
    batch = sealed(env)
    raw, receipt = pilot.MaterialDownloader(env.root / "archive").paths(
        api.reviewed(batch.materials[0])
    )
    document = json.loads(receipt.read_text())
    document["origin"] = "local_import"
    receipt.write_text(json.dumps(document))
    with pytest.raises(pilot.Blocked, match="http_html"):
        pilot.archive_check(
            env.root, batch, api.load_approvals(env.root / "approvals.json")
        )
    assert raw.stat().st_size <= 1048576


def test_unknown_job_db_is_only_read_never_adopted(environment):
    env = environment
    initialize(env)
    approve(env)
    database = env.root / "jobs/jobs.sqlite3"
    for name in (".operations.lock", "worker.lock", ".bootstrap.lock"):
        (env.root / "jobs" / name).touch(mode=0o600)
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA user_version=99")
        connection.execute("CREATE TABLE foreign_data (id INTEGER)")
    database.chmod(0o600)
    before = snapshot(env.root)
    with pytest.raises(pilot.Blocked, match="unknown_job_database_version"):
        pilot.preflight(env.root, "plan")
    assert snapshot(env.root) == before


def test_token_must_satisfy_actual_c16_authentication(environment):
    env = environment
    env.token.write_text("!" * 40)
    with pytest.raises(PermissionError):
        initialize(env)
    assert not env.root.exists()
