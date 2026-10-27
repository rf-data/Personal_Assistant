"""Native Compose config with synthetic inputs and an unreachable Docker daemon."""

import copy
import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.c26_pilot_preflight import check, main
from scripts.https_preflight import check as check_https

pytestmark = pytest.mark.external_integration
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def rendering(tmp_path_factory):
    private = tmp_path_factory.mktemp("compose-config-only")
    environment = {
        "PATH": os.defpath,
        "DOCKER_CONFIG": str(private),
        "DOCKER_HOST": "unix://" + str(private / "absent.sock"),
        "COMPOSE_DISABLE_ENV_FILE": "1",
        "C26_RUNTIME_IMAGE": "registry.synthetic.invalid/runtime@sha256:" + "a" * 64,
        "C26_GATEWAY_IMAGE": "registry.synthetic.invalid/gateway@sha256:" + "b" * 64,
        "C26_API_DNS": "api.synthetic.invalid",
        "C26_PRIVATE_API_NETWORK": "synthetic-internal",
    }
    for name in ("ROOT", "CATALOG", "CONFIG", "LIMITS"):
        environment["C26_PILOT_" + name] = "/synthetic/" + name.lower()
    environment["C26_CADDYFILE"] = "/synthetic/caddy"
    environment["C26_TLS_DIRECTORY"] = "/synthetic/tls"

    def render(profiles=(), absent=None):
        env = environment.copy()
        if absent:
            del env[absent]
        argv = [
            "docker",
            "compose",
            "--env-file",
            os.devnull,
            "-f",
            str(ROOT / "deployment/c26-pilot.compose.yaml"),
        ]
        for profile in profiles:
            argv.extend(["--profile", profile])
        result = subprocess.run(
            [*argv, "config", "--format", "json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert not (private / "absent.sock").exists()
        return result

    return render


@pytest.fixture
def candidate(rendering):
    result = rendering(["*"])
    assert result.returncode == 0, result.stderr
    return [
        json.loads(result.stdout),
        *(
            json.loads(
                (ROOT / ("deployment/c26-pilot." + name + ".json.example")).read_bytes()
            )
            for name in ("controller", "limits")
        ),
    ]


@pytest.mark.parametrize(
    "profiles,roles",
    [
        ([], set()),
        (["c26-pilot-control"], {"api", "api-gateway"}),
        (["c26-pilot-worker"], {"capacity-worker"}),
        (["*"], {"api", "api-gateway", "capacity-worker"}),
    ],
)
def test_native_profiles_do_not_start_worker_during_disabled_bootstrap(
    rendering, profiles, roles
):
    result = rendering(profiles)
    assert result.returncode == 0, result.stderr
    assert set(json.loads(result.stdout).get("services", {})) == roles


def test_native_disabled_pilot_contract_is_readonly_and_never_a_release(candidate):
    before = copy.deepcopy(candidate)
    result = check(*candidate)
    assert result["deployment_permitted"] is False
    assert result["execution_enabled"] is False
    assert result["production_release"] == "HOLD"
    assert before == candidate


@pytest.mark.parametrize(
    "absent",
    [
        "C26_PILOT_ROOT",
        "C26_PILOT_CONFIG",
        "C26_PILOT_LIMITS",
        "C26_RUNTIME_IMAGE",
        "C26_GATEWAY_IMAGE",
        "C26_PRIVATE_API_NETWORK",
        "C26_TLS_DIRECTORY",
    ],
)
def test_missing_host_or_image_binding_refuses_render(rendering, absent):
    assert rendering(["*"], absent).returncode != 0


@pytest.mark.parametrize(
    "damage",
    [
        "execution",
        "gate",
        "v1",
        "test_authority",
        "queue",
        "root",
        "budget",
        "port",
        "socket",
        "writable_config",
        "foreign_queue",
        "network",
        "image",
        "restart",
        "health",
        "cpu",
        "swap",
        "privileged",
        "environment",
        "extra_service",
        "route",
        "command",
        "nested_source",
    ],
)
def test_unsafe_effective_runtime_refused(candidate, damage):
    document, settings, limits = candidate
    api = document["services"]["api"]
    if damage == "execution":
        settings["execution_enabled"] = True
    elif damage == "gate":
        settings["deployment_gate_required"] = False
    elif damage == "v1":
        settings["deployment_gate_protocol"] = "c26-gate-v1"
    elif damage == "test_authority":
        settings["coordinator_test_required"] = True
    elif damage == "queue":
        settings["max_jobs"] = 2
    elif damage == "root":
        settings["root"] = "/synthetic/foreign"
    elif damage == "budget":
        limits["job_bytes"] *= 2
    elif damage == "port":
        api["ports"] = [{"published": "8016", "target": 8016}]
    elif damage == "socket":
        api["volumes"].append({"target": "/var/run/docker.sock"})
    elif damage == "writable_config":
        api["volumes"][-1]["read_only"] = False
    elif damage == "foreign_queue":
        document["services"]["capacity-worker"]["volumes"][0]["source"] = (
            "/synthetic/foreign"
        )
    elif damage == "network":
        document["services"]["capacity-worker"]["network_mode"] = "host"
    elif damage == "image":
        api["image"] = "runtime:latest"
    elif damage == "restart":
        api["restart"] = "always"
    elif damage == "health":
        api["healthcheck"]["test"] = ["CMD", "true"]
    elif damage == "cpu":
        api["cpus"] = "2"
    elif damage == "swap":
        api["memswap_limit"] = -1
    elif damage == "privileged":
        api["privileged"] = True
    elif damage == "environment":
        api["environment"] = {"TOKEN": "synthetic_marker"}
    elif damage == "extra_service":
        document["services"]["another-worker"] = api
    elif damage == "route":
        api["labels"]["traefik.enable"] = "true"
    elif damage == "command":
        api["command"] = ["sleep", "infinity"]
    elif damage == "nested_source":
        api["volumes"][1]["source"] = api["volumes"][0]["source"] + "/nested"
    with pytest.raises((ValueError, KeyError)):
        check(*candidate)


def test_missing_configuration_cli_is_fixed_and_secret_free(tmp_path, capsys):
    args = []
    for name in ("compose", "controller", "limits"):
        args.extend(["--" + name, str(tmp_path / "synthetic_secret_marker")])
    assert main(args) == 2
    output = capsys.readouterr()
    assert json.loads(output.out)["deployment_permitted"] is False
    assert "synthetic_secret_marker" not in output.out + output.err


@pytest.mark.parametrize("enabled", [False, True])
def test_native_pilot_ui_keeps_existing_https_contract_and_manual_lifecycle(
    tmp_path, enabled
):
    from test_c26g_readiness import OPTIONS
    from test_c26g_readiness import candidate as https_candidate
    from test_c26h_compose import rendered

    render = rendered.__wrapped__(tmp_path)
    ui = render("ui", ["*"] if enabled else [], ui_overlay="c26-pilot.ui.compose.yaml")
    if not enabled:
        assert not ui.get("services")
        return
    assert ui["services"]["ui"]["restart"] == "no"
    assert ui["services"]["ui"]["cpus"] == 0.5
    assert ui["services"]["ui"]["tmpfs"] == [
        "/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777"
    ]
    projected = copy.deepcopy(ui)
    projected["services"]["ui"]["restart"] = "unless-stopped"
    _, synthetic_ui, _ = https_candidate.__wrapped__()
    assert (
        projected["services"]["ui"]["labels"]
        == synthetic_ui["services"]["ui"]["labels"]
    )
    check_https(projected, profile="private-https", service="ui", **OPTIONS)
