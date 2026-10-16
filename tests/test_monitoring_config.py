"""Offline config checks use isolated copies and syntax-only Compose commands."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

from scripts.validate_monitoring import main, native_checks
from src.core.monitoring_validation import (
    DATA_MOUNTS,
    IMAGES,
    load_yaml,
    mount_parts,
    validate_monitoring,
    validate_overrides,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def configs(tmp_path):
    root = tmp_path / "repo"
    (root / "docker").mkdir(parents=True)
    shutil.copy(ROOT / "docker/docker-compose.monitoring.yaml", root / "docker")
    shutil.copytree(ROOT / "monitoring", root / "monitoring")
    return root


def test_checked_in_contract_and_yaml():
    assert validate_monitoring(ROOT) == []
    for path in (ROOT / "monitoring").rglob("*.yaml"):
        assert load_yaml(path)
    assert load_yaml(ROOT / "docker/docker-compose.ml.yaml")  # observed, not modified


def test_no_inline_credentials_or_active_synthetic_targets():
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, str):
                    assert not re.search(
                        r"(?i)(password|passwd|api_key|access_token|smtp_auth_password|credentials)$",
                        str(key),
                    )
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            assert not re.search(r"://[^/\s]+:[^/\s]+@", value)

    walk(load_yaml(ROOT / "docker/docker-compose.monitoring.yaml"))
    for path in (ROOT / "monitoring").rglob("*.yaml"):
        walk(load_yaml(path))
    assert not list((ROOT / "monitoring/prometheus/targets").glob("*.json"))
    for path in (ROOT / "monitoring/prometheus/target-examples").glob("*.example"):
        groups = json.loads(path.read_text())
        assert all(
            re.fullmatch(r"[A-Za-z0-9_-]+:[0-9]+", target)
            for group in groups
            for target in group["targets"]
        )


def test_runtime_data_and_secret_files_remain_ignored():
    paths = [
        "monitoring/grafana/data/database.db",
        "monitoring/alertmanager/data/silences",
        "monitoring/portainer/data/portainer.db",
        "monitoring/prometheus/data/wal",
        "monitoring/prometheus/targets/pipeline.json",
        "monitoring/.env",
        ".env.monitoring",
    ]
    result = subprocess.run(
        ["git", "check-ignore", *paths],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert set(result.stdout.splitlines()) == set(paths)


@pytest.mark.parametrize(
    "mutation",
    [
        "public",
        "socket",
        "capabilities",
        "privileged",
        "health",
        "data",
        "auto-create",
        "image",
        "profile",
        "network",
        "anonymous",
        "secret",
    ],
)
def test_unsafe_compose_changes_detected(configs, mutation):
    path = configs / "docker/docker-compose.monitoring.yaml"
    config = load_yaml(path)
    service = config["services"]["grafana"]
    if mutation == "public":
        service["ports"] = ["0.0.0.0:3000:3000"]
    if mutation == "socket":
        service["volumes"].append("/var/run/docker.sock:/var/run/docker.sock:ro")
    if mutation == "capabilities":
        service["cap_drop"] = []
    if mutation == "privileged":
        service["privileged"] = True
    if mutation == "health":
        service["healthcheck"] = {}
    if mutation == "data":
        service["volumes"][0]["source"] = "../new-grafana"
    if mutation == "auto-create":
        service["volumes"][0]["bind"]["create_host_path"] = True
    if mutation == "image":
        service["image"] = "grafana/grafana:latest"
    if mutation == "profile":
        config["services"]["portainer"].pop("profiles")
    if mutation == "network":
        config["networks"]["monitoring"]["internal"] = False
    if mutation == "anonymous":
        service["environment"]["GF_AUTH_ANONYMOUS_ENABLED"] = "true"
    if mutation == "secret":
        service["environment"]["GF_SECURITY_ADMIN_PASSWORD"] = "synthetic-bad-example"
    path.write_text(yaml.safe_dump(config))
    assert validate_monitoring(configs)


def test_data_paths_preserved_and_config_mounts_read_only():
    compose = load_yaml(ROOT / "docker/docker-compose.monitoring.yaml")
    for name, pair in DATA_MOUNTS.items():
        assert pair in [
            mount_parts(m)[:2] for m in compose["services"][name]["volumes"]
        ]
    assert not compose.get("volumes")  # no replacement named volumes
    assert not compose["services"]["cAdvisor"].get("devices")
    assert not any(
        arg.startswith("--storage.path")
        for arg in compose["services"]["alert_manager"]["command"]
    )


def test_invalid_alertmanager_and_fake_dashboard_zeros(configs):
    path = configs / "monitoring/prometheus.yaml"
    config = load_yaml(path)
    config["alerting"]["alertmanagers"][0]["static_configs"][0]["targets"] = [
        "alertmanager: 9093"
    ]
    path.write_text(yaml.safe_dump(config))
    assert "Incorrect Alertmanager DNS/port" in validate_monitoring(configs)
    path = configs / "monitoring/grafana/dashboards/pa-pipeline-v1.json"
    dashboard = json.loads(path.read_text())
    dashboard["panels"][1]["targets"][0]["expr"] = "up or vector(0)"
    path.write_text(json.dumps(dashboard))
    assert "Dashboard fabricates missing zeros" in validate_monitoring(configs)


def test_duplicate_yaml_keys_and_bad_input(configs, tmp_path):
    path = configs / "monitoring/prometheus.yaml"
    path.write_text("global: {}\nglobal: {}\n")
    with pytest.raises(ValueError, match="Duplicate"):
        load_yaml(path)
    assert main(["--root", str(configs)]) == 2
    assert main(["--root", str(tmp_path / "absent")]) == 2


def test_reports_repeat_and_no_overwrite(tmp_path):
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    assert main(["--output", str(first)]) == 0
    assert main(["--output", str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()
    before = first.read_bytes()
    assert main(["--output", str(first)]) == 2
    assert first.read_bytes() == before
    link = tmp_path / "symlink.json"
    link.symlink_to(first)
    assert main(["--output", str(link)]) == 2
    assert first.read_bytes() == before


def overrides():
    return {
        key + "_DIGEST": "a" * 64
        for key in ("ALERTMANAGER", "NODE_EXPORTER", "PORTAINER")
    }


def test_overrides_do_not_allow_tags_or_bind_addresses():
    env = overrides()
    assert validate_overrides(env) == []
    assert validate_overrides({})
    for value in ("latest", "0" * 64, "a" * 63, "A" * 64):
        assert validate_overrides({**env, "PORTAINER_DIGEST": value})
    for value in ("0.0.0.0:3000", "80", "65536", "abc"):
        assert validate_overrides({**env, "GRAFANA_PORT": value})
    assert not validate_overrides({**env, "GRAFANA_PORT": "3300"})


def compose_config(*profiles, extra=None):
    if not shutil.which("docker"):
        pytest.skip("Docker CLI unavailable; no daemon is required")
    env = {
        "PATH": os.environ.get("PATH", ""),
        **overrides(),
        "GRAFANA_ADMIN_PASSWORD_FILE": "/not-read/syntax-only",
    }
    env.update(extra or {})
    command = [
        "docker",
        "compose",
        "--env-file",
        "/dev/null",
        "-f",
        str(ROOT / "docker/docker-compose.monitoring.yaml"),
    ]
    for profile in profiles:
        command.extend(["--profile", profile])
    with tempfile.TemporaryDirectory(prefix="pa-compose-test-") as scratch:
        env["DOCKER_CONFIG"] = scratch
        result = subprocess.run(
            [*command, "config", "--format", "json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_native_compose_default_and_all_profiles():
    default = compose_config()
    assert set(default["services"]) == {"prometheus", "grafana", "alert_manager"}
    full = compose_config("host", "containers", "admin", extra={"GRAFANA_PORT": "3300"})
    assert set(full["services"]) == set(IMAGES)
    assert full["services"]["grafana"]["ports"][0]["published"] == "3300"
    assert all(
        port["host_ip"] == "127.0.0.1"
        for service in full["services"].values()
        for port in service["ports"]
    )


def test_missing_native_tools_report_not_run(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    checks = native_checks(ROOT)
    assert checks and all(c["status"] == "not_run" for c in checks)


def test_cli_runs_without_keys_network_or_services(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.validate_monitoring",
            "--output",
            str(tmp_path / "report.json"),
        ],
        cwd=ROOT,
        env={"PATH": os.environ.get("PATH", "")},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / "report.json").read_text())["structural_errors"] == []
