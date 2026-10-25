"""Synthetic source bundles, grants and receipts; no real HTTP or host mounts."""

import fcntl
import json
import os
import socket
import sqlite3
import stat
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
def environment(tmp_path, monkeypatch, private_umask):
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


@pytest.fixture
def bootstrap_targets(environment):
    env = environment
    return SimpleNamespace(
        root=env.mounts[0] / "cs50_pilot_bootstrap_test",
        policy=env.mounts[3] / "bootstrap.paths.json",
        token=env.mounts[3] / "bootstrap.token",
        env=env,
    )


def simulated_bootstrap(target, monkeypatch):
    # Nonprivileged contract tests model the administrator only. The separately
    # opted-in root test below exercises real chown and a genuinely dropped UID.
    uid, gid = os.getuid(), os.getgid()
    with monkeypatch.context() as admin:
        admin.setattr(os, "getuid", lambda: 0)
        admin.setattr(os, "geteuid", lambda: 0)
        result = pilot.bootstrap(target.root, target.policy, target.token, uid, gid)
    monkeypatch.setenv(runtime_paths.POLICY_ENV, str(target.policy))
    return result


def test_bootstrap_explicit_handoff_and_worker_initialization(
    bootstrap_targets, monkeypatch
):
    t = bootstrap_targets
    parents = {p: p.stat() for p in t.env.mounts}
    assert simulated_bootstrap(t, monkeypatch)["worker_uid"] == os.getuid()
    assert (
        pilot.verify_bootstrap(t.root, t.token)["status"] == "worker_handoff_verified"
    )
    assert all(
        g["owner_uid"] == os.getuid() for g in json.loads(t.policy.read_text())["roots"]
    )
    assert len(t.token.read_text().strip()) >= 32
    assert {p.name for p in t.root.iterdir()} == {pilot.BOOTSTRAP}
    with pytest.raises(pilot.Blocked, match="pilot_destination_exists"):
        pilot.initialize(t.env.bundle, t.root, "synthetic-operator", t.token)
    result = pilot.initialize(
        t.env.bundle, t.root, "synthetic-operator", t.token, prepared=True
    )
    assert result["status"] == "awaiting_operator_approval"
    assert (t.root / ".init-claimed").is_dir()
    assert not (t.root / "operator.token").exists()
    assert pilot.operator_token(t.root) == t.token
    assert pilot.inputs(t.root)[3].subject == "synthetic-operator"
    with pytest.raises(pilot.Blocked, match="not_pristine"):
        pilot.initialize(
            t.env.bundle, t.root, "synthetic-operator", t.token, prepared=True
        )
    for p, before in parents.items():
        after = p.stat()
        assert (before.st_uid, before.st_gid, before.st_mode) == (
            after.st_uid,
            after.st_gid,
            after.st_mode,
        )


def test_bootstrap_requires_actual_administrator(bootstrap_targets):
    t = bootstrap_targets
    if os.getuid() == 0:
        pytest.skip("Non-root denial is exercised by the dropped-UID test")
    with pytest.raises(pilot.Blocked, match="requires_root"):
        pilot.bootstrap(t.root, t.policy, t.token, 1000, 1000)
    assert not t.root.exists() and not t.policy.exists() and not t.token.exists()


@pytest.mark.parametrize("target", ["root", "policy", "token"])
def test_bootstrap_refuses_existing_targets(bootstrap_targets, monkeypatch, target):
    t = bootstrap_targets
    path = getattr(t, target)
    path.mkdir() if target == "root" else path.write_bytes(b"unchanged")
    before = path.stat()
    with pytest.raises(pilot.Blocked, match="destination_exists"):
        simulated_bootstrap(t, monkeypatch)
    assert path.stat().st_ino == before.st_ino
    if target != "root":
        assert path.read_bytes() == b"unchanged"


@pytest.mark.parametrize(
    "mutation", ["uid", "gid", "mount", "token", "policy", "extra", "permissions"]
)
def test_worker_rejects_changed_handoff(bootstrap_targets, monkeypatch, mutation):
    t = bootstrap_targets
    simulated_bootstrap(t, monkeypatch)
    if mutation in {"uid", "gid"}:
        receipt = json.loads((t.root / pilot.BOOTSTRAP).read_text())
        receipt["worker_" + mutation] += 1
        (t.root / pilot.BOOTSTRAP).write_text(json.dumps(receipt))
    elif mutation == "mount":
        t.env.identities[t.env.mounts[0]] = dict(
            t.env.identities[t.env.mounts[0]], device="8:99"
        )
    elif mutation in {"token", "policy"}:
        getattr(t, mutation).write_bytes(b"changed")
    elif mutation == "extra":
        (t.root / "unexpected").mkdir()
    else:
        t.root.chmod(0o750)
    with pytest.raises((ValueError, OSError)):
        pilot.verify_bootstrap(t.root, t.token)
    assert not (t.root / "inputs").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "nested_root",
        "code",
        "symlink",
        "traversal",
        "nested_mount",
        "missing_mount",
        "untrusted",
        "root_worker",
        "large_uid",
        "large_gid",
        "same_file",
    ],
)
def test_admin_bootstrap_rejects_unsafe_paths(bootstrap_targets, monkeypatch, mutation):
    t = bootstrap_targets
    uid, gid = os.getuid(), os.getgid()
    if mutation == "nested_root":
        t.root = t.root / "cs50_pilot_nested"
    elif mutation == "code":
        t.root = pilot.CODE / "cs50_pilot_code"
    elif mutation == "symlink":
        t.root.symlink_to(t.env.root)
    elif mutation == "traversal":
        t.root = t.root / ".." / "cs50_pilot_traversal"
    elif mutation == "nested_mount":
        t.env.identities[t.root / "nested"] = dict(t.env.identities[t.env.mounts[0]])
    elif mutation == "missing_mount":
        t.env.identities.pop(t.env.mounts[3])
    elif mutation == "untrusted":
        t.env.mounts[3].chmod(0o777)
    elif mutation == "root_worker":
        uid = 0
    elif mutation == "large_uid":
        uid = 2**31
    elif mutation == "large_gid":
        gid = 2**31
    else:
        t.token = t.policy
    monkeypatch.setattr(os, "getuid", lambda: 0)
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    with pytest.raises((ValueError, OSError)):
        pilot.bootstrap(t.root, t.policy, t.token, uid, gid)
    assert not t.policy.exists() and not t.token.exists()


def test_admin_creation_failure_preserves_evidence(bootstrap_targets, monkeypatch):
    t = bootstrap_targets
    real_open = os.open

    def denied(path, *args, **kwargs):
        if path == t.policy.name:
            raise PermissionError("synthetic create denial")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", denied)
    with pytest.raises(PermissionError):
        simulated_bootstrap(t, monkeypatch)
    assert t.root.is_dir() and not t.policy.exists() and not t.token.exists()
    with pytest.raises(pilot.Blocked, match="destination_exists"):
        simulated_bootstrap(t, monkeypatch)


def test_admin_mount_change_during_creation_blocks_handoff(
    bootstrap_targets, monkeypatch
):
    t = bootstrap_targets
    original = pilot.mountpoints
    calls = 0

    def changed():
        nonlocal calls
        calls += 1
        if calls == 3:
            t.env.identities[t.env.mounts[0]] = dict(
                t.env.identities[t.env.mounts[0]], device="8:99"
            )
        return original()

    monkeypatch.setattr(pilot, "mountpoints", changed)
    with pytest.raises(pilot.Blocked, match="mount_identity_changed"):
        simulated_bootstrap(t, monkeypatch)
    assert not (t.root / pilot.BOOTSTRAP).exists()


def test_bootstrap_claim_blocks_interrupted_initialization(
    bootstrap_targets, monkeypatch
):
    t = bootstrap_targets
    simulated_bootstrap(t, monkeypatch)
    (t.root / ".init-claimed").mkdir(mode=0o700)
    with pytest.raises(pilot.Blocked, match="not_pristine"):
        pilot.initialize(
            t.env.bundle, t.root, "synthetic-operator", t.token, prepared=True
        )
    assert not (t.root / "inputs").exists()


@pytest.mark.parametrize(
    "problem",
    [
        "read_only",
        "unreadable_mounts",
        "chown_denied",
        "token_symlink",
        "configuration_symlink",
    ],
)
def test_bootstrap_permission_and_kernel_failures(
    bootstrap_targets, monkeypatch, problem
):
    t = bootstrap_targets
    if problem == "read_only":
        t.env.identities[t.env.mounts[3]] = dict(
            t.env.identities[t.env.mounts[3]], writable=False
        )
    elif problem == "unreadable_mounts":

        def unavailable():
            raise PermissionError("synthetic mountinfo denial")

        monkeypatch.setattr(runtime_paths, "mounts", unavailable)
    elif problem == "chown_denied":

        def denied(*_args):
            raise PermissionError("synthetic ownership denial")

        monkeypatch.setattr(os, "fchown", denied)
    elif problem == "token_symlink":
        t.token.symlink_to(t.env.token)
    else:
        alias = pilot.CODE / "configuration-alias"
        alias.symlink_to(t.env.mounts[3], target_is_directory=True)
        t.policy = alias / "bootstrap.paths.json"
    with pytest.raises((ValueError, OSError)):
        simulated_bootstrap(t, monkeypatch)
    assert not (t.root / pilot.BOOTSTRAP).exists()


def test_privileged_root_owned_mounts_real_worker_handoff(
    bootstrap_targets, monkeypatch, request
):
    if os.getuid() != 0 or os.environ.get("C26_BOOTSTRAP_PRIVILEGED_TESTS") != "1":
        pytest.skip(
            "Requires explicitly enabled local root test on synthetic roots only"
        )
    t = bootstrap_targets
    # Permit traversal of only this test's freshly created pytest hierarchy.
    base = request.config.option.basetemp
    assert base is not None and "c26b3" in str(base)
    parent = pilot.CODE.parent
    while parent.is_relative_to(base):
        parent.chmod(0o711)
        if parent == base:
            break
        parent = parent.parent
    pilot.CODE.chmod(0o755)
    for p in t.env.mounts:
        p.chmod(0o755)
        assert (p.stat().st_uid, p.stat().st_gid) == (0, 0)
    for name in ("cs50_python",):
        (t.env.bundle / name).chmod(0o755)
    t.env.bundle.chmod(0o755)
    for name in (
        *pilot.SNAPSHOTS,
        "manifest.json",
        "binding.json",
        "cs50_pilot.py",
        "files.json",
    ):
        (t.env.bundle / name).chmod(0o644)
    before = {
        p: (p.stat().st_uid, p.stat().st_gid, p.stat().st_mode) for p in t.env.mounts
    }
    assert pilot.bootstrap(t.root, t.policy, t.token, 1000, 1000)["worker_uid"] == 1000
    monkeypatch.setenv(runtime_paths.POLICY_ENV, str(t.policy))
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            os.setgroups([])
            os.setgid(1000)
            os.setuid(1000)
            assert not os.access(t.env.mounts[0], os.W_OK)
            assert not os.access(t.env.mounts[3], os.W_OK)
            try:
                pilot.bootstrap(t.root, t.policy, t.token, 1000, 1000)
            except pilot.Blocked:
                pass
            else:
                raise AssertionError("Worker gained administrative rights")
            pilot.verify_bootstrap(t.root, t.token)
            result = pilot.initialize(
                t.env.bundle, t.root, "synthetic-operator", t.token, prepared=True
            )
            assert result["status"] == "awaiting_operator_approval"
            assert pilot.inputs(t.root)[3].subject == "synthetic-operator"
            assert not (t.root / "operator.token").exists()
            os.write(write_fd, b"passed")
            os._exit(0)
        except BaseException as error:
            os.write(write_fd, type(error).__name__.encode())
            os._exit(1)
    os.close(write_fd)
    outcome = os.read(read_fd, 256)
    os.close(read_fd)
    _, status = os.waitpid(child, 0)
    assert status == 0, outcome.decode()
    assert outcome == b"passed"
    assert {
        p: (p.stat().st_uid, p.stat().st_gid, p.stat().st_mode) for p in t.env.mounts
    } == before
    for p in (t.root, t.root / "jobs", t.policy, t.token):
        assert (p.stat().st_uid, p.stat().st_gid) == (1000, 1000)
        assert stat.S_IMODE(p.stat().st_mode) == (0o700 if p.is_dir() else 0o600)


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


@pytest.mark.parametrize("prepared", [False, True])
def test_generated_configuration_runs_one_real_synthetic_workflow(
    environment, monkeypatch, prepared
):
    env = environment
    if prepared:
        target = SimpleNamespace(
            root=env.mounts[0] / "cs50_pilot_e2e",
            policy=env.mounts[3] / "e2e.paths.json",
            token=env.mounts[3] / "e2e.token",
        )
        simulated_bootstrap(target, monkeypatch)
        env.root, env.policy, env.token = target.root, target.policy, target.token
        pilot.initialize(
            env.bundle, env.root, "synthetic-review-operator", env.token, prepared=True
        )
    else:
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
            pilot.operator_token(env.root),
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
            pilot.operator_token(env.root),
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
