"""Native config rendering only: synthetic paths and an unreachable Docker daemon."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from test_c26g_readiness import OPTIONS, candidate

from scripts.c26h_preflight import check

pytestmark = pytest.mark.external_integration
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def rendered(tmp_path):
    docker = shutil.which("docker")
    assert docker is not None, (
        "Explicit native config checks require Docker Compose CLI"
    )
    config = tmp_path / "docker-config"
    config.mkdir()
    environment = {
        "PATH": os.defpath,
        "DOCKER_CONFIG": str(config),
        "DOCKER_HOST": "unix://" + str(tmp_path / "no-daemon.sock"),
        "COMPOSE_DISABLE_ENV_FILE": "1",
        "C26_RUNTIME_IMAGE": "registry.synthetic.invalid/runtime@sha256:" + "b" * 64,
        "C26_GATEWAY_IMAGE": "registry.synthetic.invalid/gateway@sha256:" + "c" * 64,
        "C26_UI_IMAGE": "registry.synthetic.invalid/ui@sha256:" + "a" * 64,
        "C26_API_DNS": "api.synthetic.invalid",
        "C26_PRIVATE_API_NETWORK": "synthetic-api",
        "C26_INGRESS_NETWORK": "synthetic-ingress",
        "C26_BACKEND_NETWORK": "synthetic-api",
        "C26_UI_ORIGIN": OPTIONS["origin"],
        "C26_TRUSTED_PROXY_CIDRS": "172.20.0.2/32",
        "ADMIN_OIDC_ISSUER": "https://issuer.synthetic.invalid",
        "ADMIN_OPERATOR_SUBJECTS": '["owner"]',
        "JOB_API_IDENTITIES": "[]",
        "JOB_API_URL": "https://api.synthetic.invalid:8443",
        "C26_ROUTE_ID": "synthetic",
        "C26_ALLOWED_CIDRS": "10.8.0.0/24",
    }
    for key in (
        "C26_HOST_RUNTIME",
        "C26_HOST_DATA",
        "C26_HOST_CONFIGURATION",
        "C26_HOST_LOGS",
        "C26_HOST_CACHE",
        "C26_CADDYFILE",
        "C26_TLS_DIRECTORY",
        "C26_UI_TOKENS",
        "C26_UI_OIDC",
        "C26_API_CA",
    ):
        environment[key] = "/synthetic/" + key.lower()
    # Explicit test stand-in for Coolify-generated labels, never host evidence.
    _, ui, _ = candidate.__wrapped__()
    labels = tmp_path / "synthetic-ingress.compose.json"
    labels.write_text(
        json.dumps({"services": {"ui": {"labels": ui["services"]["ui"]["labels"]}}})
    )

    def render(kind, profiles, *, ui_overlay="c26h.staging.ui.compose.yaml"):
        files = (
            ["coolify.runtime-bootstrap.compose.yaml", "c26h.staging.compose.yaml"]
            if kind == "backend"
            else [
                "coolify.ui.compose.yaml",
                "coolify.private-https.yaml",
                ui_overlay,
            ]
        )
        command = [docker, "compose", "--env-file", os.devnull]
        for name in files:
            command += ["-f", str(ROOT / "deployment" / name)]
        if kind == "ui":
            command += ["-f", str(labels)]
        for profile in profiles:
            command += ["--profile", profile]
        result = subprocess.run(
            [*command, "config", "--format", "json"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert not (tmp_path / "no-daemon.sock").exists()
        return json.loads(result.stdout)

    return render


@pytest.mark.parametrize(
    "profiles,roles",
    [
        ([], set()),
        (["c26-runtime-approved"], {"api-gateway", "api"}),
        (["c26-worker-approved"], {"capacity-worker"}),
        (["*"], {"api-gateway", "api", "capacity-worker"}),
    ],
)
def test_backend_profiles_stay_inactive_without_opt_in(rendered, profiles, roles):
    assert set(rendered("backend", profiles).get("services", {})) == roles


@pytest.mark.parametrize("profiles,count", [([], 0), (["*"], 1)])
def test_ui_profile_stays_inactive_without_opt_in(rendered, profiles, count):
    assert len(rendered("ui", profiles).get("services", {})) == count


def test_native_rendered_pair_keeps_all_live_gates_closed(rendered):
    values = [
        json.loads((ROOT / "deployment" / name).read_bytes())
        for name in (
            "c26g.staging.controller.json.example",
            "c26h.staging.content.json.example",
            "c26h.staging.review.json.example",
            "c26h.staging.search.json.example",
        )
    ]
    result = check(
        rendered("backend", ["*"]), rendered("ui", ["*"]), *values, **OPTIONS
    )
    assert result["production_release"] == "HOLD"
    assert result["deployment_permitted"] is False
