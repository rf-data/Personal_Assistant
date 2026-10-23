"""Offline bootstrap checks with synthetic files and no queue connections."""

import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from scripts import c26_runtime_preflight as module
from src.job_control.controller import authenticate
from src.job_control.models import Settings
from src.tools_materials.capacity import CapacityLimits

REPO = Path(__file__).resolve().parents[1]
IMAGE = "registry.invalid/fixture@sha256:" + "a" * 64
pytestmark = pytest.mark.skipif(
    "deployment_gate_required" not in Settings.model_fields,
    reason="Explicit integration dependency #148",
)


@pytest.fixture
def staged(tmp_path, monkeypatch):
    point = tmp_path / "runtime-state"
    point.mkdir(mode=0o700)
    root = point / "c16"
    root.mkdir(mode=0o700)
    config, limits = tmp_path / "controller.json", tmp_path / "limits.json"
    data = json.loads(
        (REPO / "deployment/c26-runtime.controller.json.example").read_text()
    )
    assert data["root"] == "/app/runtime-state/c16"
    data["root"] = str(root)
    config.write_text(json.dumps(data))
    limits.write_bytes(
        (REPO / "deployment/c26-runtime.limits.json.example").read_bytes()
    )
    config.chmod(0o600)
    limits.chmod(0o600)
    monkeypatch.setattr(
        module,
        "mounts",
        lambda: {point: dict(filesystem="ext4", root="/synthetic-bind", writable=True)},
    )
    monkeypatch.setattr(
        shutil,
        "disk_usage",
        lambda _: shutil._ntuple_diskusage(30 << 30, 10 << 30, 20 << 30),
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Offline preflight must never open SQLite")

    monkeypatch.setattr(sqlite3, "connect", forbidden)
    return config, limits, point, root


def check(staged, image=IMAGE):
    config, limits, point, _ = staged
    return module.inspect(config, limits, point, image, IMAGE)


def test_disabled_templates_validate_without_queue_or_identities(staged):
    config, limits, _, root = staged
    assert CapacityLimits.model_validate_json(limits.read_bytes()).max_materials == 1
    settings = Settings.model_validate_json(config.read_bytes())
    for token in (None, "Bearer arbitrary", "Bearer " + "a" * 64):
        with pytest.raises(PermissionError):
            authenticate(settings, token)
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    report = check(staged)
    assert report["queue_status"] == "uninitialized"
    assert report["queue_healthy"] is False
    assert report["execution_enabled"] is False
    assert report["deployment_permitted"] is False
    assert report["required_free_bytes"] == 6123683840
    assert {p.name: p.read_bytes() for p in root.iterdir()} == before == {}
    (root / "jobs.sqlite3").write_bytes(b"not a healthy queue")
    assert check(staged)["queue_status"] == "present_unverified"
    assert (root / "jobs.sqlite3").read_bytes() == b"not a healthy queue"


@pytest.mark.parametrize(
    "change",
    [
        {"execution_enabled": True},
        {"workflows_enabled": True},
        {"pdf_enabled": True},
        {"index_jobs_enabled": True},
        {"import_jobs_enabled": True},
        {"deployment_gate_required": False},
        {"max_parallel": 2},
        {"max_queued": 2},
        {"max_jobs": 2},
        {"root": "relative/root"},
        {"unknown_setting": True},
        {
            "identities": [
                {
                    "subject": "synthetic",
                    "role": "operator",
                    "courses": ["cs50_python"],
                    "token_sha256": "a" * 64,
                }
            ]
        },
    ],
)
def test_refuses_unsafe_staging_config(staged, change):
    config, _, _, root = staged
    data = json.loads(config.read_bytes())
    data.update(change)
    config.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        check(staged)
    assert list(root.iterdir()) == []


@pytest.mark.parametrize(
    "change",
    [
        {"reserve_bytes": (5 << 30) - 1},
        {"job_bytes": 513 << 20},
        {"max_materials": 2},
        {"archive_bytes": 65 << 20},
        {"catalog_bytes": 129 << 20},
        {"report_bytes": 17 << 20},
        {"enabled": False},
    ],
)
def test_refuses_limit_increases_or_invented_flags(staged, change):
    _, limits, _, _ = staged
    data = json.loads(limits.read_bytes())
    data.update(change)
    limits.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        check(staged)


@pytest.mark.parametrize("image", ["", "fixture:latest", "fixture@sha256:bad"])
def test_refuses_missing_immutable_image_binding(staged, image):
    with pytest.raises(ValueError):
        check(staged, image)


@pytest.mark.parametrize(
    "reason",
    ["missing", "readonly", "ephemeral", "capacity", "root-mode", "quarantine"],
)
def test_refuses_mount_capacity_and_root_failures(staged, monkeypatch, reason):
    _, _, point, root = staged
    if reason in {"missing", "readonly", "ephemeral"}:
        monkeypatch.setattr(
            module,
            "mounts",
            lambda: (
                {}
                if reason == "missing"
                else {
                    point: dict(
                        filesystem="tmpfs" if reason == "ephemeral" else "ext4",
                        root="/bind",
                        writable=reason != "readonly",
                    )
                }
            ),
        )
    elif reason == "capacity":
        monkeypatch.setattr(
            shutil, "disk_usage", lambda _: shutil._ntuple_diskusage(1, 1, 0)
        )
    elif reason == "root-mode":
        root.chmod(0o755)
    else:
        (root / "quarantine").touch()
    with pytest.raises(ValueError):
        check(staged)


def test_cli_refuses_without_creating_queue(staged, capsys):
    config, limits, point, root = staged
    args = [
        "--config",
        str(config),
        "--limits",
        str(limits),
        "--runtime-mount",
        str(point),
        "--runtime-image",
        IMAGE,
        "--gateway-image",
        IMAGE,
    ]
    assert module.main(args) == 0
    assert json.loads(capsys.readouterr().out)["queue_healthy"] is False
    assert module.main(args[:-1] + ["unbound:latest"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "blocked"
    assert list(root.iterdir()) == []
