"""Preparation contracts and refused starts. No Docker CLI or host access."""

import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

from scripts.cs50_worker import main
from src.job_control.models import Settings
from src.tools_materials.capacity import CapacityLimits

REPO = Path(__file__).resolve().parents[1]


def test_candidate_preserves_loopback_namespace_and_single_capacity_worker():
    data = yaml.safe_load(
        (REPO / "deployment/coolify.runtime-bootstrap.compose.yaml").read_text()
    )
    services = data["services"]
    assert set(services) == {"api-gateway", "api", "capacity-worker"}
    api, worker = services["api"], services["capacity-worker"]
    assert api["network_mode"] == "service:api-gateway" and "networks" not in api
    assert worker["network_mode"] == "none" and "networks" not in worker
    assert api["entrypoint"] == ["python", "-m", "scripts.deployment"]
    assert worker["entrypoint"] == ["python", "-m", "scripts.cs50_worker"]
    assert api["image"] == worker["image"]
    assert "--limits" in worker["command"]
    assert data["networks"]["private-api"]["external"] is True
    assert set(services["api-gateway"]["networks"]) == {"private-api"}
    for name, service in services.items():
        assert not service.get("ports") and not service.get("build")
        assert service["profiles"] == [
            "c26-worker-approved"
            if name == "capacity-worker"
            else "c26-runtime-approved"
        ]
        # Raw Compose in Coolify 4.4.7 appends numeric list entries; a mapping
        # would become a mixed mapping when management labels are appended.
        assert service["labels"] == ["traefik.enable=false"]
        assert service["read_only"] and service["cap_drop"] == ["ALL"]
        assert service["restart"] == "no" and service["pull_policy"] == "never"
        assert service["mem_limit"] == service["memswap_limit"]
        assert service["healthcheck"]["test"][0] == "CMD"
        for mount in service["volumes"]:
            assert mount["bind"]["create_host_path"] is False
            assert mount["target"] != "/var/run/docker.sock"
            # The 4.4.7 bind-source validator accepts simple references; the
            # Compose extension must still reject every missing/empty path.
            variable = re.fullmatch(r"\$\{([A-Z0-9_]+)\}", mount["source"])
            assert variable
            name = variable[1]
            assert data["x-required-paths"][name].startswith("${" + name + ":?")
    assert next(m for m in api["volumes"] if m["target"] == "/app/data")["read_only"]
    assert api["volumes"] == worker["volumes"]
    assert {m["target"] for m in api["volumes"]} == {
        "/app/runtime-state",
        "/app/data",
        "/app/configuration",
        "/app/logs",
        "/app/.cache",
    }
    assert next(m for m in api["volumes"] if m["target"] == "/app/configuration")[
        "read_only"
    ]
    assert (
        api["environment"]
        == worker["environment"]
        == {
            "PA_PERSISTENT_ROOTS_FILE": "/app/configuration/c26-runtime/persistent-roots.json"
        }
    )


@pytest.mark.parametrize("reason", ["disabled", "parallel", "capacity", "quarantine"])
def test_capacity_worker_refuses_before_creating_queue(tmp_path, monkeypatch, reason):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    settings = Settings(
        root=root,
        execution_enabled=reason != "disabled",
        max_parallel=2 if reason == "parallel" else 1,
    )
    config, limits = tmp_path / "controller.json", tmp_path / "limits.json"
    config.write_text(settings.model_dump_json())
    limits.write_text(CapacityLimits().model_dump_json())
    config.chmod(0o600)
    limits.chmod(0o600)
    if reason == "capacity":
        monkeypatch.setattr(
            shutil, "disk_usage", lambda _: shutil._ntuple_diskusage(1024, 1024, 0)
        )
    if reason == "quarantine":
        (root / "quarantine").write_text("owned synthetic marker")
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    assert main(["--config", str(config), "--limits", str(limits)]) == 2
    after = {p.name: p.read_bytes() for p in root.iterdir()}
    assert all(after[name] == raw for name, raw in before.items())
    # A refused start may reserve the existing C22 maintenance-lock filename;
    # this is not queue initialization and must not be removed to force startup.
    assert set(after) - set(before) <= {".operations.lock"}
    if ".operations.lock" in after:
        assert after[".operations.lock"] == b""
        assert (root / ".operations.lock").stat().st_mode & 0o777 == 0o600
    assert not (root / "jobs.sqlite3").exists()


def test_required_gate_refuses_missing_existing_queue(tmp_path):
    if "deployment_gate_required" not in Settings.model_fields:
        pytest.skip("Requires the explicitly pending deployment-gate PR #148")
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    config, limits = tmp_path / "controller.json", tmp_path / "limits.json"
    value = Settings(root=root, execution_enabled=True).model_dump(mode="json")
    value["deployment_gate_required"] = True
    config.write_text(json.dumps(value))
    limits.write_text(CapacityLimits().model_dump_json())
    config.chmod(0o600)
    limits.chmod(0o600)
    assert main(["--config", str(config), "--limits", str(limits)]) == 2
    assert {p.name for p in root.iterdir()} <= {".operations.lock"}
    assert not (root / "jobs.sqlite3").exists()


def test_explicit_cold_provision_keeps_gate_held_and_worker_idle(tmp_path):
    if "deployment_gate_required" not in Settings.model_fields:
        pytest.skip("Explicit integration dependency #148")
    from src.job_control.deployment_gate import Gate, require_existing_queue

    from scripts.cs50_worker import CapacityExecutor
    from src.job_control.controller import Controller
    from src.job_control.operations import health
    from src.job_control.store import Store, Unavailable

    root = tmp_path / "new-runtime"
    root.mkdir(mode=0o700)
    settings = Settings(root=root, deployment_gate_required=True, max_jobs=1)
    with pytest.raises(Unavailable):
        require_existing_queue(settings)
    assert list(root.iterdir()) == []
    # Explicit operator-equivalent provisioning only, never preflight/startup.
    Store(root, deployment_gate_required=True)
    gate = Gate(settings)
    gate.initialize()
    assert gate.status()["phase"] == "held"
    with pytest.raises(Unavailable):
        CapacityExecutor(settings, CapacityLimits())
    worker_settings = settings.model_copy(update={"execution_enabled": True})
    worker = CapacityExecutor(worker_settings, CapacityLimits())
    try:
        worker.step()
        health(worker_settings, "worker")
        assert not worker.store.all()
        assert Controller(settings).settings.execution_enabled is False
        assert gate.status()["phase"] == "held"
        with pytest.raises((Unavailable, BlockingIOError)):
            CapacityExecutor(worker_settings, CapacityLimits())
    finally:
        worker.close()
    assert gate.status()["phase"] == "held"
