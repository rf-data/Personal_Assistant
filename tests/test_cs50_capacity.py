"""Synthetic C26 capacity boundaries; no host, HTTP, images or original data."""

import json
import os
import shutil
import subprocess
from types import SimpleNamespace

import httpx
import pytest
from test_cs50_batch_worker import REPO
from test_cs50_batch_worker import offline as offline
from test_cs50_batch_worker import scope as scope

from scripts.cs50_batch import main
from scripts.cs50_worker import CapacityExecutor
from src.tools_materials import batch as api
from src.tools_materials import capacity as cap


def test_small_host_policy_and_batch_estimate(scope):
    # Versioned template is public, so validate its model without private-file loader.
    limits = cap.CapacityLimits.model_validate_json(
        (REPO / "deployment/cs50-worker.hetzner-small.limits.json.example").read_bytes()
    )
    estimate = cap.estimate(scope["batch"], limits)
    assert limits.reserve_bytes == 5 * 1024**3 and limits.max_materials == 3
    assert estimate["materials"] == 3
    assert estimate["raw_upper_bytes"] == 3 * cap.MIB
    assert estimate["required_free_before_new_batch_bytes"] > limits.reserve_bytes
    assert estimate["parser_expansion_is_not_known"] is True
    assert estimate == cap.estimate(scope["batch"], limits)
    with pytest.raises(ValueError, match="count"):
        cap.estimate(scope["batch"], limits.model_copy(update={"max_materials": 2}))


@pytest.mark.parametrize(
    "update",
    [{"reserve_bytes": 1}, {"max_materials": True}, {"job_bytes": 0}, {"unknown": 1}],
)
def test_invalid_capacity_policy(update):
    with pytest.raises(ValueError):
        cap.CapacityLimits.model_validate(update)


def test_private_policy_and_cli_environment_fail_closed(scope, monkeypatch, capsys):
    path = scope["tmp"] / "limits.json"
    api.output(path, cap.CapacityLimits().model_dump(mode="json"))
    assert cap.load_limits(path) == cap.CapacityLimits()
    path.chmod(0o644)
    with pytest.raises(ValueError, match="Private"):
        cap.load_limits(path)
    monkeypatch.setenv("C26_LIMITS_FILE", str(scope["tmp"] / "absent.json"))
    result = main(
        [
            "plan",
            "--manifest",
            str(scope["batch"].manifest),
            "--course",
            "cs50_python",
            "--output",
            str(scope["tmp"] / "not-created.json"),
        ]
    )
    assert result == 2 and not (scope["tmp"] / "not-created.json").exists()
    assert json.loads(capsys.readouterr().out)["status"] == "rejected"


def test_reserve_exact_boundary_and_projected_budget(scope, monkeypatch):
    root = scope["archive"]
    reserve = 5 * 1024**3
    monkeypatch.setattr(
        cap.shutil, "disk_usage", lambda _r: SimpleNamespace(free=reserve + 10)
    )
    assert cap.check_capacity(root, cap.MIB, reserve, 10) == 0
    with pytest.raises(ValueError, match="reserve"):
        cap.check_capacity(root, cap.MIB, reserve, 11)
    with pytest.raises(ValueError, match="projected"):
        cap.check_capacity(root, 9, reserve, 10)


def test_low_disk_blocks_download_and_catalog_before_writes(scope, monkeypatch):
    limits = cap.CapacityLimits()
    monkeypatch.setattr(
        cap.shutil,
        "disk_usage",
        lambda _r: SimpleNamespace(free=limits.reserve_bytes - 1),
    )
    with pytest.raises(ValueError, match="reserve"):
        api.obtain(
            scope["batch"],
            scope["archive"],
            scope["approvals"],
            execute=True,
            transport=scope["transport"],
        )
    target = scope["tmp"] / "catalog"
    with pytest.raises(ValueError, match="reserve"):
        api.seal(scope["batch"], scope["archive"], target, scope["approvals"])
    assert (
        not target.exists()
        and not list(scope["archive"].iterdir())
        and not scope["calls"]
    )


def test_size_scan_refuses_symlinks_and_oversized_files(scope):
    root = scope["archive"]
    outside = scope["tmp"] / "not-to-read"
    outside.write_bytes(b"synthetic")
    link = root / "link"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="Unsafe"):
        cap.tree_bytes(root, cap.MIB)
    link.unlink()
    (root / "file").write_bytes(b"123456")
    with pytest.raises(ValueError, match="byte budget"):
        cap.tree_bytes(root, 5)
    assert outside.read_bytes() == b"synthetic"


def test_capacity_drop_midstream_never_publishes_raw(scope, monkeypatch):
    material = scope["batch"].materials[0]
    batch = scope["batch"].model_copy(update={"materials": (material,)})
    limits = cap.CapacityLimits()
    available = {"free": limits.reserve_bytes + 100 * cap.MIB}
    monkeypatch.setattr(
        cap.shutil, "disk_usage", lambda _r: SimpleNamespace(**available)
    )
    data = scope["payloads"][material.original_url]

    class Stream(httpx.SyncByteStream):
        def __iter__(self):
            yield data[:10]
            available["free"] = limits.reserve_bytes - 1
            yield data[10:]

    content_type = (
        "application/pdf"
        if data.startswith(b"%PDF")
        else "text/html"
        if data.startswith(b"<html")
        else "text/plain"
    )
    transport = httpx.MockTransport(
        lambda _r: httpx.Response(
            200, stream=Stream(), headers={"Content-Type": content_type}
        )
    )
    report = api.obtain(
        batch, scope["archive"], scope["approvals"], execute=True, transport=transport
    )
    assert report["materials"][0]["status"] == "failed"
    raw, receipt = api.MaterialDownloader(scope["archive"]).paths(
        api.reviewed(material)
    )
    assert not raw.exists()
    assert (
        api.ArtifactReceipt.model_validate_json(receipt.read_bytes()).status == "failed"
    )
    assert scope["payloads"][material.original_url] == data


def test_report_budget_and_single_worker_enforced(scope):
    target = scope["tmp"] / "too-large.json"
    with pytest.raises(ValueError, match="projected"):
        api.output(
            target,
            {"data": "s" * cap.MIB},
            limits=cap.CapacityLimits(report_bytes=cap.MIB),
        )
    assert not target.exists()
    with pytest.raises(ValueError, match="single"):
        CapacityExecutor(SimpleNamespace(max_parallel=2), cap.CapacityLimits())


def test_download_preview_report_uses_archive_budget(scope, capsys):
    batch_file = scope["tmp"] / "batch.json"
    api.output(
        batch_file,
        dict(
            batch=scope["batch"].model_dump(mode="json"),
            sha256=api.fingerprint(scope["batch"].model_dump(mode="json")),
        ),
    )
    # Existing originals can exceed the separate export budget: never delete them.
    original = scope["archive"] / "synthetic-existing-raw"
    with original.open("xb") as stream:
        stream.truncate(17 * cap.MIB)
    report = scope["archive"] / "preview.json"
    assert (
        main(
            [
                "download",
                "--batch",
                str(batch_file),
                "--archive",
                str(scope["archive"]),
                "--output",
                str(report),
            ]
        )
        == 0
    )
    assert json.loads(report.read_bytes())["execution_requested"] is False
    assert original.stat().st_size == 17 * cap.MIB and not scope["calls"]
    capsys.readouterr()


def test_worker_step_checks_capacity_before_dispatch(scope, monkeypatch):
    worker = object.__new__(CapacityExecutor)
    worker.settings = SimpleNamespace(root=scope["archive"])
    worker.limits, worker.next_budget_check = cap.CapacityLimits(), 0
    monkeypatch.setattr(cap.shutil, "disk_usage", lambda _r: SimpleNamespace(free=1))
    with pytest.raises(ValueError, match="reserve"):
        worker.step()  # No Store/children initialized: dispatch must not be reached.


def test_small_host_compose_render_without_daemon():
    if shutil.which("docker") is None:
        pytest.skip("Docker Compose CLI unavailable; no installation")
    env = {**os.environ, "BACKEND_DIGEST": "a" * 64}
    for key in (
        "JOBS",
        "CATALOG",
        "CONFIG",
        "ARCHIVE",
        "SPECS",
        "EXPORTS",
        "TOKEN",
        "LIMITS",
    ):
        env["C26_" + key] = "/unprovisioned/synthetic/" + key.lower()
    env["C26_EGRESS_NETWORK"] = "synthetic-unprovisioned-egress"
    run = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(REPO / "deployment/cs50-worker.hetzner-small.env.example"),
            "-f",
            str(REPO / "deployment/cs50-worker.compose.yaml"),
            "--profile",
            "processing",
            "--profile",
            "tools",
            "--profile",
            "download",
            "config",
            "--format",
            "json",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    services = json.loads(run.stdout)["services"]
    worker, cli, downloader = (
        services[n] for n in ("executor", "offline-cli", "downloader")
    )
    assert int(worker["mem_limit"]) == int(worker["memswap_limit"]) == 1024**3
    assert float(worker["cpus"]) == 1 and worker["restart"] == "no"
    assert worker["entrypoint"] == ["python", "-m", "scripts.cs50_worker"]
    assert worker["network_mode"] == cli["network_mode"] == "none"
    assert int(cli["mem_limit"]) == int(downloader["mem_limit"]) == 256 * cap.MIB
    for service in services.values():
        assert "ports" not in service and service["pull_policy"] == "never"
        policy = next(
            v
            for v in service["volumes"]
            if v["target"] == "/run/config/c26-limits.json"
        )
        assert policy["read_only"] and not policy["bind"]["create_host_path"]
