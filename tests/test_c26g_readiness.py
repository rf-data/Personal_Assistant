"""Offline configuration contracts; values are synthetic, never host settings."""

import copy
import json
import re
from pathlib import Path

import pytest
import yaml

from scripts.c26g_preflight import check, load, main
from src.job_control.models import Settings

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://ui.synthetic.invalid"
OPTIONS = dict(
    origin=ORIGIN,
    tls_router="ui-https",
    http_router="ui-http",
    middleware="synthetic-private@docker",
)
V2 = "deployment_gate_protocol" in Settings.model_fields


def render(path, values):
    """Test-only subset of interpolation/normalization, NOT a Compose renderer."""

    def replace(match):
        key, operator, default = match.groups()
        value = values.get(key)
        if operator == ":-" and not value:
            return default
        if not value:
            raise ValueError("missing_synthetic_variable")
        return value

    source = "\n".join(
        line
        for line in path.read_text().splitlines()
        if not line.lstrip().startswith("#")
    )
    text = re.sub(r"\$\{([A-Z0-9_]+)(?:(:\?|:-)([^}]*))?\}", replace, source)
    data = yaml.safe_load(text)
    for role in data["services"].values():
        if isinstance(role.get("labels"), list):
            role["labels"] = dict(v.split("=", 1) for v in role["labels"])
        if role.get("mem_limit") == "768m":
            role["mem_limit"] = 768 * 1024**2
    return data


@pytest.fixture
def candidate():
    env = dict(
        C26_UI_IMAGE="registry.synthetic.invalid/ui@sha256:" + "a" * 64,
        C26_UI_ORIGIN=ORIGIN,
        C26_INGRESS_NETWORK="synthetic-ingress",
        C26_BACKEND_NETWORK="synthetic-api",
        C26_TRUSTED_PROXY_CIDRS="172.20.0.2/32",
        ADMIN_OIDC_ISSUER="https://issuer.synthetic.invalid",
        ADMIN_OPERATOR_SUBJECTS='["owner"]',
        JOB_API_URL="https://api.synthetic.invalid:8443",
        JOB_API_IDENTITIES="[]",
        C26_UI_TOKENS="/synthetic/tokens",
        C26_UI_OIDC="/synthetic/oidc.toml",
        C26_API_CA="/synthetic/ca.crt",
    )
    ui = render(ROOT / "deployment/coolify.ui.compose.yaml", env)
    ui["services"]["ui"]["environment"]["C26_ACCESS_PROFILE"] = "private-https"
    ui["services"]["ui"]["labels"].update(
        {
            "traefik.enable": "true",
            "traefik.http.routers.ui-https.rule": "Host(`ui.synthetic.invalid`)",
            "traefik.http.routers.ui-http.rule": "Host(`ui.synthetic.invalid`)",
            "traefik.http.routers.ui-https.tls": "true",
            "traefik.http.routers.ui-https.entrypoints": "https",
            "traefik.http.routers.ui-http.entrypoints": "http",
            "traefik.http.routers.ui-https.service": "ui",
            "traefik.http.routers.ui-https.middlewares": "synthetic-private@docker",
            "traefik.http.routers.ui-http.middlewares": "redirect",
            "traefik.http.middlewares.redirect.redirectscheme.scheme": "https",
            "traefik.http.services.ui.loadbalancer.server.port": "8501",
            "traefik.http.middlewares.synthetic-private.ipallowlist.sourcerange": "10.8.0.0/24",
        }
    )
    # No backend template exists on the C26-G baseline. Its absence is an
    # explicit incompatibility test, not a fallback deployable configuration.
    path = ROOT / "deployment/coolify.runtime-bootstrap.compose.yaml"
    backend = {}
    if path.exists():
        values = {
            k: "/synthetic/" + k.lower()
            for k in (
                "C26_HOST_RUNTIME",
                "C26_HOST_DATA",
                "C26_HOST_CONFIGURATION",
                "C26_HOST_LOGS",
                "C26_HOST_CACHE",
                "C26_CADDYFILE",
                "C26_TLS_DIRECTORY",
            )
        }
        values.update(
            C26_RUNTIME_IMAGE="registry.synthetic.invalid/runtime@sha256:" + "b" * 64,
            C26_GATEWAY_IMAGE="registry.synthetic.invalid/gateway@sha256:" + "c" * 64,
            C26_API_DNS="api.synthetic.invalid",
            C26_PRIVATE_API_NETWORK="synthetic-api",
        )
        backend = render(path, values)
    controller = json.loads(
        (ROOT / "deployment/c26g.staging.controller.json.example").read_text()
    )
    return backend, ui, controller


def test_staging_requires_actual_v2_implementation(candidate):
    if V2:
        result = check(*candidate, **OPTIONS)
        assert result["production_release"] == "HOLD"
        assert result["deployment_permitted"] is False
        assert "versioned_live_gate_and_mutating_driver" in result["live_blockers"]
    else:
        with pytest.raises(ValueError):
            check(*candidate, **OPTIONS)
        assert candidate[0] == {}


@pytest.mark.parametrize(
    "damage",
    [
        "gate",
        "protocol",
        "enabled",
        "identity",
        "root",
        "network",
        "tls",
        "issuer",
        "proxy",
        "ports",
        "worker",
        "mount",
        "image",
        "restart",
        "command",
        "profile",
    ],
)
def test_invalid_configuration_refused(candidate, damage):
    backend, ui, controller = copy.deepcopy(candidate)
    if damage == "gate":
        controller["deployment_gate_required"] = False
    elif damage == "protocol":
        controller["deployment_gate_protocol"] = "c26-gate-v1"
    elif damage == "enabled":
        controller["execution_enabled"] = True
    elif damage == "identity":
        controller["identities"] = [{"subject": "unbound"}]
    elif damage == "root":
        controller["root"] = "/tmp/replacement-queue"
    elif damage == "tls":
        ui["services"]["ui"]["environment"]["JOB_API_URL"] = (
            "http://api.synthetic.invalid"
        )
    elif damage == "issuer":
        ui["services"]["ui"]["environment"]["ADMIN_OIDC_ISSUER"] = (
            "http://issuer.synthetic.invalid"
        )
    elif damage == "proxy":
        ui["services"]["ui"]["environment"]["C26_TRUSTED_PROXY_CIDRS"] = "0.0.0.0/0"
    elif V2:
        role = backend["services"]["capacity-worker"]
        if damage == "network":
            ui["networks"]["backend"]["name"] = "wrong"
        elif damage == "ports":
            role["ports"] = ["8016:8016"]
        elif damage == "worker":
            role["network_mode"] = "host"
        elif damage == "mount":
            role["volumes"][0]["bind"]["create_host_path"] = True
        elif damage == "image":
            role["image"] = "runtime:latest"
        elif damage == "restart":
            role["restart"] = "always"
        elif damage == "command":
            role["command"] = ["sleep", "infinity"]
        elif damage == "profile":
            role["profiles"] = []
    with pytest.raises((ValueError, KeyError)):
        check(backend, ui, controller, **OPTIONS)


@pytest.mark.parametrize(
    "key",
    [
        "C26_UI_IMAGE",
        "C26_UI_ORIGIN",
        "ADMIN_OIDC_ISSUER",
        "JOB_API_URL",
        "C26_UI_TOKENS",
    ],
)
def test_missing_required_environment_is_refused(key):
    # All other substitutions are nonempty synthetic values, so each removed
    # required variable is independently exercised.
    path = ROOT / "deployment/coolify.ui.compose.yaml"
    env = {k: "synthetic" for k in re.findall(r"\$\{([A-Z0-9_]+)", path.read_text())}
    del env[key]
    with pytest.raises(ValueError, match="missing_synthetic_variable"):
        render(path, env)


@pytest.mark.parametrize(
    "body",
    [
        '{"x":1,"x":2}',
        '{"x":NaN}',
        '{"x":Infinity}',
        "[" * 2000,
        "x" * (1024 * 1024 + 1),
    ],
)
def test_bounded_strict_json(tmp_path, body):
    path = tmp_path / "bad.json"
    path.write_text(body)
    with pytest.raises((ValueError, RecursionError)):
        load(path)


def test_cli_fixed_diagnostics_do_not_echo_input(tmp_path, capsys):
    secret = "synthetic_do_not_echo_this_marker"
    path = tmp_path / "private.json"
    path.write_text(json.dumps({"secret": secret}))
    args = [
        "--backend-compose-json",
        str(path),
        "--ui-compose-json",
        str(path),
        "--controller",
        str(path),
        "--origin",
        ORIGIN,
        "--tls-router",
        "ui-https",
        "--http-router",
        "ui-http",
        "--middleware",
        "synthetic-private@docker",
    ]
    assert main(args) == 2
    out = capsys.readouterr()
    assert secret not in out.out + out.err
    assert str(path) not in out.out + out.err
    assert json.loads(out.out) == dict(
        status="refused", production_release="HOLD", deployment_permitted=False
    )
