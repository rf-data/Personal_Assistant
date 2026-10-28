"""Isolated filesystem lifecycle; host commands are recorded, never executed.

Runtime protections additionally run against synthetic bytes under offline_guard.
This does not claim a real Ubuntu/systemd or frozen wheelhouse installation.
"""

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from test_cs50_batch_worker import offline as offline
from test_cs50_batch_worker import scope as scope
from test_cs50p_mvp import download_args as download_args

REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / "deployment/cs50p-download-only"


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, PACKAGE / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


installer = module("download_installer", "install.py")
pilot = module("download_entrypoint", "pilot.py")


@pytest.fixture
def sandbox(tmp_path):
    root = tmp_path / "host"
    (root / "etc/systemd/system").mkdir(parents=True)
    calls = []

    def run(argv, *, cwd=None):
        calls.append(([str(a) for a in argv], cwd))
        if list(argv[:3]) == ["python3.12", "-m", "venv"]:
            library = Path(argv[3]) / "lib/synthetic"
            library.mkdir(parents=True, mode=0o700)
            (library / "module.py").write_text("# synthetic")
            (library / "module.py").chmod(0o600)
        return ""

    source = tmp_path / "source"
    for folder in ("src", "scripts", "deployment/cs50p-download-only/runtime"):
        (source / folder).mkdir(parents=True)
    (source / "src/__init__.py").write_text("")
    (source / "scripts/__init__.py").write_text("")
    (source / "scripts/cs50p_native.py").write_text("raise AssertionError('excluded')")
    (source / "scripts/cs50_worker.py").write_text("raise AssertionError('excluded')")
    (source / "deployment/cs50p-download-only/runtime/requirements.txt").write_text(
        "# synthetic closure\n"
    )
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    (wheels / "synthetic-1.0-py3-none-any.whl").write_bytes(b"not a deployable wheel")
    specs = tmp_path / "specs"
    (specs / "snapshots").mkdir(parents=True)
    snapshot = b'{"synthetic":true}'
    (specs / "snapshots/manifest.json").write_bytes(snapshot)
    batch = dict(
        schema_version=1,
        manifest="/build/manifest.json",
        source_origin="official",
        files={"manifest.json": installer.digest(snapshot)},
        materials=[dict(synthetic=True)],
    )
    (specs / "batch.json").write_bytes(
        installer.canonical(
            dict(batch=batch, sha256=installer.digest(installer.canonical(batch)))
        )
    )
    shutil.copyfile(PACKAGE / "limits.json.example", specs / "limits.json")
    shutil.copyfile(PACKAGE / "approvals.json.example", specs / "approvals.json")
    api = installer.Installer(root, run, (os.getuid(), os.getgid()))
    return api, source, wheels, specs, calls


def install(sandbox, release="r1"):
    api, source, wheels, specs, _ = sandbox
    return api.install(source, wheels, specs, release)


def test_install_repeat_upgrade_rollback_uninstall_preserves_data(sandbox):
    api, source, wheels, specs, calls = sandbox
    assert install(sandbox)["status"] == "installed_stopped"
    first_calls = len(calls)
    first = os.readlink(api.base / "current")
    (api.data / "reports/operator-evidence.json").write_text("keep")
    (api.data / "archive/material").write_bytes(b"persistent")
    assert not (api.base / first / "app/scripts/cs50p_native.py").exists()
    assert not (api.base / first / "app/scripts/cs50_worker.py").exists()
    assert (api.base / first / "app/scripts").stat().st_mode & 0o777 == 0o755
    assert (api.base / first / "venv/lib/synthetic").stat().st_mode & 0o777 == 0o755
    assert (
        api.base / first / "venv/lib/synthetic/module.py"
    ).stat().st_mode & 0o777 == 0o644
    assert (api.base / first / "specs").stat().st_mode & 0o777 == 0o700
    assert (api.base / first / "specs/limits.json").stat().st_mode & 0o777 == 0o600
    relocated = json.loads((api.base / first / "specs/batch.json").read_bytes())
    assert relocated["batch"]["manifest"] == str(
        api.base / first / "specs/snapshots/manifest.json"
    )
    install(sandbox)
    assert not any("venv" in argv for argv, _ in calls[first_calls:])
    (source / "src/__init__.py").write_text("# upgraded\n")
    install(sandbox, "r2")
    assert os.readlink(api.base / "current") == "releases/r2"
    assert api.rollback("r1")["status"] == "rolled_back_stopped"
    assert os.readlink(api.base / "current") == first
    assert api.uninstall()["status"] == "uninstalled"
    assert api.uninstall()["status"] == "uninstalled"
    assert not (api.units / installer.UNIT).exists()
    assert (api.data / "archive/material").read_bytes() == b"persistent"
    assert (api.data / "reports/operator-evidence.json").read_text() == "keep"
    assert all(os.readlink(api.units / name) == "/dev/null" for name in installer.MASKS)
    install(sandbox, "r2")  # reinstall after uninstall; retained data and masks
    for argv, _ in calls:
        assert argv[:2] not in (["systemctl", "start"], ["systemctl", "enable"])
        assert argv[0] not in {"docker", "ssh", "apt", "userdel"}
    pip = next(argv for argv, _ in calls if "install" in argv)
    assert {"--no-index", "--require-hashes", "--only-binary=:all:"} <= set(pip)


@pytest.mark.parametrize(
    "kind",
    ["data", "unit", "mask", "dropin", "timer", "symlink", "transient", "control"],
)
def test_unknown_host_artifacts_refused_without_mutation(sandbox, kind):
    api, *_ = sandbox
    if kind == "data":
        api.data.mkdir(parents=True)
        (api.data / "precious").write_text("keep")
    elif kind == "unit":
        (api.units / installer.UNIT).write_text("foreign")
    elif kind == "mask":
        (api.units / "cs50p-worker.service").write_text("foreign")
    elif kind == "dropin":
        (api.units / "cs50p-download-only.service.d").mkdir()
    elif kind == "timer":
        (api.units / "cs50p-download-only.timer").touch()
    elif kind in {"transient", "control"}:
        folder = api.root / (
            "run/systemd/transient"
            if kind == "transient"
            else "etc/systemd/system.control"
        )
        folder.mkdir(parents=True)
        if kind == "transient":
            (folder / "cs50p-native@job.service").touch()
        else:
            (folder / "cs50p-download-only.service.d").mkdir()
    else:
        api.base.parent.mkdir(parents=True)
        api.base.symlink_to(api.root / "foreign")
    with pytest.raises((ValueError, FileNotFoundError)):
        install(sandbox)
    assert not (api.units / "cs50p-native@.service").is_symlink()


def test_active_service_blocks_install_upgrade_rollback_uninstall(sandbox):
    api, *_ = sandbox
    install(sandbox)
    pointer = os.readlink(api.base / "current")
    api.run = lambda *_a, **_k: "cs50p-download-only.service loaded activating start"
    for action in (
        lambda: install(sandbox, "r2"),
        lambda: api.rollback("r1"),
        api.uninstall,
    ):
        with pytest.raises(ValueError, match="Stop existing"):
            action()
    assert os.readlink(api.base / "current") == pointer


def test_missing_wheel_or_runtime_failure_never_switches_release(sandbox):
    api, *_ = sandbox
    install(sandbox)
    previous = api.run

    def fail(argv, **kwargs):
        if "pip" in argv:
            raise subprocess.CalledProcessError(1, argv)
        return previous(argv, **kwargs)

    api.run = fail
    with pytest.raises(subprocess.CalledProcessError):
        install(sandbox, "r2")
    assert os.readlink(api.base / "current") == "releases/r1"
    assert (api.base / "releases/r2").exists()
    assert not (api.base / "releases/r2/ready.json").exists()
    with pytest.raises(FileNotFoundError):
        install(sandbox, "r2")


@pytest.mark.parametrize(
    "kind", ["batch", "snapshot", "extra", "release", "id", "instance"]
)
def test_integrity_and_identity_fail_closed(sandbox, kind):
    api, source, wheels, specs, _ = sandbox
    if kind in {"release", "id", "instance"}:
        install(sandbox)
    if kind == "batch":
        (specs / "batch.json").write_text('{"batch":{},"sha256":"bad"}')
    elif kind == "snapshot":
        (specs / "snapshots/manifest.json").write_bytes(b"changed")
    elif kind == "extra":
        (specs / "controller.json").write_text("{}")
    elif kind == "release":
        (api.base / "releases/r1/app/src/__init__.py").write_text("changed")
    elif kind == "id":
        (source / "src/__init__.py").write_text("different package")
    else:
        (api.units / "cs50p-native@job.service").write_text("override template mask")
    with pytest.raises((ValueError, KeyError)):
        install(sandbox)


def test_download_only_wrapper_real_admission_and_persistence(scope, download_args):
    from scripts import cs50p_mvp
    from src.tools_materials import batch as api

    # Synthetic fixture bytes deliberately relabelled in-memory for schema coverage only.
    # No synthetic approvals are delivered as a host configuration.
    batch = api.plan(
        scope["batch"].manifest,
        ["cs50_python"],
        [scope["batch"].materials[0].source_id],
        synthetic=False,
    )
    download_args.batch.rename(download_args.batch.with_name("synthetic-batch.json"))
    api.output(
        download_args.batch,
        dict(
            batch=batch.model_dump(mode="json"),
            sha256=api.fingerprint(batch.model_dump(mode="json")),
        ),
    )
    assert (
        pilot.check(download_args.batch.parent, download_args.archive.parent)[
            "processing_enabled"
        ]
        is False
    )
    report, code = cs50p_mvp.download(download_args, transport=scope["transport"])
    assert code == 0 and report["status"] == "completed"
    assert list(download_args.reports.glob("download-*.json"))
    assert (
        pilot.check(download_args.batch.parent, download_args.archive.parent)["status"]
        == "checked"
    )
    # No jobs, enrollment, grant or controller is produced by either check/download.
    assert not list(download_args.archive.parent.rglob("*.sqlite3"))
    assert not (download_args.archive.parent / "jobs").exists()


def test_wrapper_has_no_worker_or_native_command(capsys):
    with pytest.raises(SystemExit) as error:
        pilot.main(["worker"])
    assert error.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


@pytest.mark.parametrize("scenario", ["preflight", "download", "tampered", "locked"])
def test_installed_entrypoint_with_seal_and_real_lifecycle_lock(
    scope, download_args, monkeypatch, capsys, scenario
):
    import fcntl

    from scripts import cs50p_mvp
    from src.tools_materials import batch as api

    root = download_args.batch.parent
    script = root / "app/scripts/cs50p_download_only.py"
    script.parent.mkdir(parents=True)
    script.write_text("# synthetic installed path")
    specs = root / "specs"
    specs.mkdir(mode=0o700)
    for name in ("limits.json", "approvals.json"):
        (root / name).rename(specs / name)
    batch = api.plan(
        scope["batch"].manifest,
        ["cs50_python"],
        [scope["batch"].materials[0].source_id],
        synthetic=False,
    )
    api.output(
        specs / "batch.json",
        dict(
            batch=batch.model_dump(mode="json"),
            sha256=api.fingerprint(batch.model_dump(mode="json")),
        ),
    )
    files = {
        "specs/" + p.name: installer.digest(p.read_bytes()) for p in specs.iterdir()
    }
    (root / "ready.json").write_text(json.dumps(dict(files=files)))
    lockfile = root / "install.lock"
    lockfile.touch()
    original_open = os.open

    def redirected_open(path, *a, **k):
        if str(path) == "/opt/.cs50p-download-only-install.lock":
            path = lockfile
        return original_open(path, *a, **k)

    monkeypatch.setattr(pilot, "__file__", str(script))
    monkeypatch.setattr(
        pilot,
        "Path",
        lambda p: root if str(p) == "/var/lib/cs50p-download-only" else Path(p),
    )
    monkeypatch.setattr(os, "open", redirected_open)
    original_download = cs50p_mvp.download
    monkeypatch.setattr(
        cs50p_mvp,
        "download",
        lambda args: original_download(args, transport=scope["transport"]),
    )
    monkeypatch.setattr(
        cs50p_mvp, "check_worker", lambda *_a, **_k: pytest.fail("C16 forbidden")
    )
    with lockfile.open("rb") as lock:
        if scenario == "locked":
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if scenario == "tampered":
            (specs / "approvals.json").write_text("{}")
        code = pilot.main(["download" if scenario == "download" else "preflight"])
    value = json.loads(capsys.readouterr().out)
    assert code == (2 if scenario in {"locked", "tampered"} else 0)
    assert value["status"] == (
        "blocked" if code else "completed" if scenario == "download" else "checked"
    )
    assert len(scope["calls"]) == int(scenario == "download")
    assert not (root / "jobs").exists()


@pytest.mark.parametrize("case", ["missing", "corrupt"])
def test_real_artifact_guard_blocks_before_release_mutation(sandbox, case):
    api, source, wheels, specs, calls = sandbox
    guard = module("wheelhouse_guard", "wheelhouse.py")
    wheel = next(wheels.iterdir())
    requirement = source / "deployment/cs50p-download-only/runtime/requirements.txt"
    requirement.write_text(
        "synthetic==1.0 --hash=sha256:" + installer.digest(wheel.read_bytes()) + "\n"
    )
    previous = api.run

    def run(argv, **kwargs):
        if str(installer.PACKAGE / "wheelhouse.py") in list(map(str, argv)):
            guard.check(wheels, requirement)
        return previous(argv, **kwargs)

    api.run = run
    install(sandbox)
    if case == "missing":
        wheel.unlink()
        # Keep the directory nonempty to reach the complete artifact guard.
        (wheels / "unreviewed-1.0-py3-none-any.whl").write_bytes(b"unreviewed")
    else:
        wheel.write_bytes(b"corrupt")
    with pytest.raises(ValueError):
        install(sandbox, "r2")
    assert os.readlink(api.base / "current") == "releases/r1"
    assert not (api.base / "releases/r2").exists()
