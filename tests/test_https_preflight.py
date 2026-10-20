"""Audit real Compose CLI output plus mutated unsafe routing configurations."""

import copy
import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.https_preflight import Refused, check

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://ui.synthetic.invalid"


def render(tmp_path, profile):
    env = dict(
        os.environ,
        C26_UI_IMAGE="registry.synthetic.invalid/ui@sha256:" + "a" * 64,
        C26_UI_ORIGIN=ORIGIN,
        C26_INGRESS_NETWORK="synthetic-ingress",
        C26_BACKEND_NETWORK="synthetic-api",
        C26_TRUSTED_PROXY_CIDRS="172.20.0.2/32",
        C26_ROUTE_ID="synthetic-ui",
        C26_ALLOWED_CIDRS="10.8.0.0/24",
        ADMIN_OIDC_ISSUER="https://issuer.synthetic.invalid",
        ADMIN_OPERATOR_SUBJECTS='["owner"]',
        JOB_API_URL="https://api.synthetic.invalid:8443",
        JOB_API_IDENTITIES="[]",
        C26_UI_TOKENS=str(tmp_path / "tokens"),
        C26_UI_OIDC=str(tmp_path / "secrets.toml"),
        C26_API_CA=str(tmp_path / "ca.crt"),
    )
    completed = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(ROOT / "deployment/coolify.ui.compose.yaml"),
            "-f",
            str(ROOT / ("deployment/coolify." + profile + ".yaml")),
            "config",
            "--format",
            "json",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert completed.returncode == 0, "Compose rendering failed"
    data = json.loads(completed.stdout)
    # Simulate only Coolify-generated labels, then audit the FULL real rendered
    # Compose structure. This is not a live Coolify or routing proof.
    data["services"]["ui"]["labels"].update(
        {
            "traefik.enable": "true",
            "traefik.http.routers.ui-https.rule": "Host(`ui.synthetic.invalid`)",
            "traefik.http.routers.ui-http.rule": "Host(`ui.synthetic.invalid`)",
            "traefik.http.routers.ui-https.tls": "true",
            "traefik.http.routers.ui-https.entrypoints": "https",
            "traefik.http.routers.ui-http.entrypoints": "http",
            "traefik.http.routers.ui-https.service": "ui",
            "traefik.http.routers.ui-https.middlewares": "synthetic-ui-private@docker",
            "traefik.http.routers.ui-http.middlewares": "redirect",
            "traefik.http.middlewares.redirect.redirectscheme.scheme": "https",
            "traefik.http.services.ui.loadbalancer.server.port": "8501",
        }
    )
    return data


def audit(data, profile="private-https"):
    return check(
        data,
        origin=ORIGIN,
        profile=profile,
        tls_router="ui-https",
        http_router="ui-http",
        service="ui",
        middleware="synthetic-ui-private@docker",
    )


@pytest.mark.parametrize("profile", ["private-https", "public-https"])
def test_profiles_use_real_compose_and_explicit_gate(tmp_path, profile):
    assert (
        audit(render(tmp_path, profile), profile)["production_release"]
        == "production_release_blocked"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "ports",
        "entrypoint",
        "extra_cap",
        "tcp_route",
        "worker",
        "image",
        "read_only",
        "health",
        "network",
        "mount",
        "auth",
        "router",
        "backend_route",
        "redirect",
        "tls",
        "allowlist",
        "all_ips",
        "spoofed_ips",
        "untrusted_proxy",
        "shared_network",
    ],
)
def test_unsafe_renderings_refused(tmp_path, mutation):
    data = render(tmp_path, "private-https")
    ui = data["services"]["ui"]
    labels = ui["labels"]
    if mutation == "ports":
        ui["ports"] = [{"published": "8501", "target": 8501}]
    elif mutation == "entrypoint":
        ui["entrypoint"] = ["python", "-m", "streamlit"]
    elif mutation == "extra_cap":
        ui["cap_add"] = ["SYS_ADMIN"]
    elif mutation == "tcp_route":
        labels["traefik.tcp.routers.hidden.rule"] = "HostSNI(`*`)"
    elif mutation == "worker":
        data["services"]["worker"] = copy.deepcopy(ui)
    elif mutation == "image":
        ui["image"] = "ui:latest"
    elif mutation == "read_only":
        ui["read_only"] = False
    elif mutation == "health":
        ui["healthcheck"]["disable"] = True
    elif mutation == "network":
        ui["network_mode"] = "host"
    elif mutation == "mount":
        ui["volumes"][0]["target"] = "/var/run/docker.sock"
    elif mutation == "auth":
        ui["environment"]["ADMIN_AUTH_MODE"] = "demo"
    elif mutation == "router":
        labels["traefik.http.routers.ui-https.rule"] += " || Host(`foreign.invalid`)"
    elif mutation == "backend_route":
        labels["traefik.http.routers.backend.rule"] = "Host(`api.synthetic.invalid`)"
    elif mutation == "redirect":
        del labels["traefik.http.middlewares.redirect.redirectscheme.scheme"]
    elif mutation == "tls":
        labels["traefik.http.routers.ui-https.tls"] = "false"
    elif mutation == "allowlist":
        labels["traefik.http.routers.ui-https.middlewares"] = ""
    elif mutation == "all_ips":
        labels[
            "traefik.http.middlewares.synthetic-ui-private.ipallowlist.sourcerange"
        ] = "0.0.0.0/0"
    elif mutation == "spoofed_ips":
        labels[
            "traefik.http.middlewares.synthetic-ui-private.ipallowlist.ipstrategy.depth"
        ] = "1"
    elif mutation == "untrusted_proxy":
        ui["environment"]["C26_TRUSTED_PROXY_CIDRS"] = "0.0.0.0/0"
    elif mutation == "shared_network":
        data["networks"]["backend"]["name"] = data["networks"]["ingress"]["name"]
    with pytest.raises((Refused, ValueError)):
        audit(data)


def test_missing_operator_inputs_prevent_compose_start(tmp_path):
    completed = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            "/dev/null",
            "-f",
            str(ROOT / "deployment/coolify.ui.compose.yaml"),
            "config",
            "--quiet",
        ],
        env={"PATH": os.defpath},
        capture_output=True,
        timeout=15,
    )
    assert completed.returncode != 0


def test_coolify_root_path_and_camelcase_entrypoints(tmp_path):
    data = render(tmp_path, "public-https")
    labels = data["services"]["ui"]["labels"]
    for name in ("ui-http", "ui-https"):
        key = "traefik.http.routers." + name
        labels[key + ".rule"] += " && PathPrefix(`/`)"
        labels[key + ".entryPoints"] = labels.pop(key + ".entrypoints")
    audit(data, "public-https")
