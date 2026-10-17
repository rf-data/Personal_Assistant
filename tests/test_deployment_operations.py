"""C22 synthetic-only persistence, maintenance fence and failure tests."""

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.deployment import main
from scripts.job_control_demo import DEMO_TOKEN, build_inputs
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.models import Identity, Settings
from src.job_control.operations import (
    backup,
    fence,
    health,
    inventory,
    preflight,
    restore,
    volume_probe,
)


@pytest.fixture
def scope(tmp_path):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    settings = Settings(
        root=root,
        catalog=build_inputs(tmp_path),
        execution_enabled=True,
        identities=(
            Identity(
                subject="synthetic",
                role="operator",
                courses=("cs50_python",),
                token_sha256=hashlib.sha256(DEMO_TOKEN.encode()).hexdigest(),
            ),
        ),
    )
    config = tmp_path / "controller.json"
    config.write_text(settings.model_dump_json())
    config.chmod(0o600)
    controller = Controller(settings)
    return settings, config, controller


def test_volume_probe_and_readonly_preflight(scope):
    settings, config, _ = scope
    before = inventory(settings.root)
    assert preflight(config) == settings
    assert before == inventory(settings.root)
    assert all(volume_probe(settings.root).values())
    assert before == inventory(settings.root)


@pytest.mark.parametrize(
    "kind",
    [
        "missing_root",
        "public_root",
        "public_config",
        "missing_config",
        "low_disk",
        "quarantine",
        "wrong_owner",
        "not_writable",
        "bad_catalog",
    ],
)
def test_preflight_refuses_bad_environment(scope, monkeypatch, kind):
    settings, config, _ = scope
    if kind == "missing_root":
        settings = settings.model_copy(update={"root": settings.root.parent / "absent"})
        config.write_text(settings.model_dump_json())
    elif kind == "public_root":
        settings.root.chmod(0o755)
    elif kind == "public_config":
        config.chmod(0o644)
    elif kind == "missing_config":
        config.unlink()
    elif kind == "low_disk":
        monkeypatch.setattr(
            shutil, "disk_usage", lambda _: shutil._ntuple_diskusage(1024, 1024, 0)
        )
    elif kind == "quarantine":
        (settings.root / "quarantine").write_text("synthetic\n")
    elif kind == "wrong_owner":
        monkeypatch.setattr(os, "getuid", lambda: os.geteuid() + 1)
    elif kind == "not_writable":
        monkeypatch.setattr(os, "access", lambda *args: False)
    else:
        entry = next(iter(settings.catalog.values()))
        (entry.root / next(iter(entry.files))).write_text("corrupted synthetic input")
    with pytest.raises((OSError, ValueError)):
        preflight(config)


def test_maintenance_fence_refuses_backup_while_managed_role_active(scope, tmp_path):
    settings, config, _ = scope
    with fence(settings.root):
        with pytest.raises(BlockingIOError):
            backup(config, tmp_path / "snapshot")
    assert not (tmp_path / "snapshot").exists()


def test_full_snapshot_restore_hashes_catalog_idempotence_and_quarantine(
    scope, tmp_path
):
    settings, config, controller = scope
    # Exercise existing C16/C18 storage names, including non-JSON artifacts.
    (settings.root / "workflows/synthetic/requests").mkdir(parents=True, mode=0o700)
    (settings.root / "workflows/synthetic/state.v1.json").write_text(
        '{"source_origin":"synthetic"}'
    )
    (settings.root / "workflows/synthetic/requests/idempotence.json").write_text(
        '{"request":"synthetic"}'
    )
    actor = controller.authenticate("Bearer " + DEMO_TOKEN)
    preview = controller.preview(
        actor,
        dict(
            process_id="material_planning",
            parameters=dict(
                source_ref="demo_snapshots", course_id="cs50_python", section="0"
            ),
        ),
    )
    request = dict(preview=preview.model_dump(mode="json"), confirmed=True, start=False)
    job = controller.create(actor, request, "synthetic_c22_request_0001")
    controller.store.transition(
        job.job_id, "interrupted", "interrupted", "Synthetic interrupted state"
    )
    controller.store.heartbeat(0)
    (settings.root / "quarantine").write_text(job.job_id)
    snapshot, target = tmp_path / "snapshot", tmp_path / "restored"
    manifest = backup(config, snapshot)
    assert "workspace/jobs.sqlite3" in manifest["files"]
    assert not any(
        name.endswith(("-wal", "-shm", ".token")) for name in manifest["files"]
    )
    report = restore(snapshot, target)
    assert report["activated"] is False and report["jobs"] == 1
    assert (target / "quarantine").read_bytes() == (
        settings.root / "quarantine"
    ).read_bytes()
    restored = Controller(settings.model_copy(update={"root": target}))
    assert restored.get(actor, job.job_id).status == "interrupted"
    assert (
        restored.create(actor, request, "synthetic_c22_request_0001").job_id
        == job.job_id
    )
    assert (
        inventory(target)["workflows/synthetic/state.v1.json"]
        == inventory(settings.root)["workflows/synthetic/state.v1.json"]
    )
    for ref, entry in settings.catalog.items():
        for name, expected in entry.files.items():
            assert (
                hashlib.sha256(
                    (snapshot / "catalog" / ref / name).read_bytes()
                ).hexdigest()
                == expected
            )
    with pytest.raises(ValueError):
        backup(config, snapshot)
    with pytest.raises(ValueError):
        restore(snapshot, target)


def test_refuses_nonterminal_or_unclean_worker(scope, tmp_path):
    settings, config, controller = scope
    controller.store.heartbeat()
    with pytest.raises(ValueError, match="cleanly"):
        backup(config, tmp_path / "live-heartbeat")
    controller.store.heartbeat(0)
    actor = controller.authenticate("Bearer " + DEMO_TOKEN)
    preview = controller.preview(
        actor,
        dict(
            process_id="material_planning",
            parameters=dict(
                source_ref="demo_snapshots", course_id="cs50_python", section="0"
            ),
        ),
    )
    controller.create(
        actor,
        dict(preview=preview.model_dump(mode="json"), confirmed=True, start=False),
        "synthetic_c22_pending_0001",
    )
    with pytest.raises(ValueError, match="terminal"):
        backup(config, tmp_path / "nonterminal")


@pytest.mark.parametrize(
    "damage", ["bytes", "extra", "manifest", "symlink", "hardlink"]
)
def test_restore_rejects_tampering_before_creating_destination(scope, tmp_path, damage):
    _, config, _ = scope
    snapshot, target = tmp_path / "snapshot", tmp_path / "target"
    backup(config, snapshot)
    if damage == "bytes":
        (snapshot / "workspace/jobs.sqlite3").write_bytes(b"invalid sqlite")
    elif damage == "extra":
        (snapshot / "unexpected.token").write_text("synthetic")
    elif damage == "manifest":
        (snapshot / "manifest.json").write_text('{"schema_version":9}')
    elif damage == "symlink":
        (snapshot / "link").symlink_to(config)
    else:
        os.link(config, snapshot / "link")
    with pytest.raises(ValueError):
        restore(snapshot, target)
    assert not target.exists()


def test_health_never_creates_db_and_stale_worker_fails(scope):
    settings, _, controller = scope
    with pytest.raises(ValueError):
        health(settings, "worker")
    executor = Executor(settings)
    try:
        controller.store.heartbeat()
        health(settings, "worker")
    finally:
        executor.close()
    with pytest.raises(ValueError):
        health(settings, "worker")
    with pytest.raises(OSError):
        health(settings.model_copy(update={"root": settings.root / "absent"}), "worker")
    assert not (settings.root / "absent").exists()


def test_cli_only_explicit_paths(scope, capsys):
    _, config, _ = scope
    assert main(["check", "--config", str(config)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ready"
    with pytest.raises(SystemExit):
        main(["backup"])


def test_snapshot_preserves_input_files_named_like_runtime_locks(scope, tmp_path):
    settings, config, _ = scope
    directory = settings.root / "retained-source"
    directory.mkdir(mode=0o700)
    for name in ("worker.lock", "execution.lock", "jobs.sqlite3-wal"):
        (directory / name).write_bytes(b"synthetic source bytes")
    backup(config, tmp_path / "snapshot")
    restore(tmp_path / "snapshot", tmp_path / "restored")
    assert inventory(tmp_path / "restored/retained-source") == inventory(directory)


def test_production_roles_network_storage_and_limits():
    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "deployment/compose.yaml").read_text())
    services = config["services"]
    assert config["networks"]["private"]["internal"] is True
    assert services["api"]["network_mode"] == "service:api-gateway"
    assert services["executor"]["network_mode"] == "none"
    assert services["api"]["volumes"] == services["executor"]["volumes"]
    assert not services["ui"]["volumes"] == services["api"]["volumes"]
    for service in services.values():
        assert service["profiles"] == ["private-production"]
        assert service["pull_policy"] == "never"
        assert service["user"] == "10001:10001"
        assert service["read_only"] and service["cap_drop"] == ["ALL"]
        assert service["pids_limit"] <= 512 and service["cpus"] <= 2
        assert (
            "ports" not in service
            and "privileged" not in service
            and "pid" not in service
        )
        assert service["healthcheck"]["test"][0] == "CMD"
        assert service["stop_grace_period"] == "30s"
        for volume in service.get("volumes", []):
            assert volume["bind"]["create_host_path"] is False
            assert "docker.sock" not in volume["source"]
    monitoring = yaml.safe_load(
        (root / "deployment/monitoring.compose.yaml").read_text()
    )
    assert set(monitoring["services"]) == {"prometheus", "grafana"}
    for service in monitoring["services"].values():
        assert service["profiles"] == ["private-monitoring"] and "ports" not in service
    scrape = yaml.safe_load((root / "deployment/prometheus.yaml").read_text())[
        "scrape_configs"
    ][0]
    assert scrape["scheme"] == "https"
    assert scrape["authorization"]["credentials_file"] == "/run/secrets/metrics.token"
    assert "insecure_skip_verify" not in scrape["tls_config"]
    assert scrape["sample_limit"] == 5000 and scrape["target_limit"] == 1


def test_runtime_lock_is_exact_subset_of_repository_lock():
    import tomllib

    root = Path(__file__).resolve().parents[1]
    original = {
        p["name"]: p for p in tomllib.loads((root / "uv.lock").read_text())["package"]
    }
    subset = tomllib.loads((root / "deployment/runtime/uv.lock").read_text())["package"]
    for package in subset:
        if package["name"] == "personal-assistant-job-runtime":
            continue
        assert package["version"] == original[package["name"]]["version"]
        assert package.get("wheels") == original[package["name"]].get("wheels")


def test_compose_cli_resolves_only_explicit_profiles(tmp_path):
    if not shutil.which("docker"):
        pytest.skip("blocked: local Docker Compose CLI unavailable; no download")
    repo = Path(__file__).resolve().parents[1]
    source = (repo / "deployment/compose.yaml").read_text() + (
        repo / "deployment/monitoring.compose.yaml"
    ).read_text()
    empty = tmp_path / "empty.env"
    empty.touch()
    environment = {"PATH": os.defpath}
    for name in set(re.findall(r"\$\{([A-Z0-9_]+)", source)):
        environment[name] = (
            "0" * 64 if name.endswith("_DIGEST") else str(tmp_path / name)
        )
    environment.update(
        C22_API_DNS="jobs.example.invalid",
        C22_INGRESS_NETWORK="c22-synthetic",
        C22_UI_ENV=str(empty),
    )
    for profiles, expected in (
        ([], 0),
        (["private-production"], 4),
        (["private-production", "private-monitoring"], 6),
    ):
        command = [
            "docker",
            "compose",
            "--env-file",
            str(empty),
            "-f",
            "deployment/compose.yaml",
            "-f",
            "deployment/monitoring.compose.yaml",
        ]
        for profile in profiles:
            command.extend(["--profile", profile])
        command.extend(["config", "--format", "json"])
        result = subprocess.run(
            command,
            cwd=repo,
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        resolved = json.loads(result.stdout)
        assert len(resolved["services"]) == expected
