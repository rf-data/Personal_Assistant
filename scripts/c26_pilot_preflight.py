"""Read-only review of rendered pilot Compose; never grants execution/deployment."""

import argparse
import json
import re
from pathlib import Path

from scripts.c26g_preflight import load
from scripts.https_preflight import require
from src.job_control.deployment_gate import IMAGE
from src.job_control.models import Settings
from src.tools_materials.capacity import CapacityLimits

ROOT = "/var/lib/personal-assistant/private"
CONFIG = "/run/config/controller.json"
BUDGETS = {
    "api-gateway": (0.10, 256 * 1024**2, 64),
    "api": (0.25, 512 * 1024**2, 64),
    "capacity-worker": (1.0, 1024 * 1024**2, 128),
}


def check(document, controller, limits):
    """Check the disabled bootstrap contract, without opening runtime stores."""
    settings = Settings.model_validate(controller)
    limits = CapacityLimits.model_validate(limits)
    require(str(settings.root) == ROOT, "pilot_root_required")
    require(
        settings.deployment_gate_required
        and settings.deployment_gate_protocol == "c26-gate-v2"
        and not settings.coordinator_test_required,
        "mandatory_v2_without_test_authority",
    )
    require(
        not any(
            getattr(settings, key)
            for key in (
                "execution_enabled",
                "workflows_enabled",
                "pdf_enabled",
                "index_jobs_enabled",
                "import_jobs_enabled",
            )
        ),
        "disabled_bootstrap_required",
    )
    require(
        settings.max_jobs == settings.max_queued == settings.max_parallel == 1,
        "single_job_required",
    )
    require(not settings.catalog and not settings.identities, "unbound_bootstrap_only")
    require(
        limits.reserve_bytes >= 2 * 1024**3
        and limits.job_bytes <= 128 * 1024**2
        and limits.catalog_bytes <= 1024**2
        and limits.report_bytes <= 8 * 1024**2
        and limits.max_materials == 1,
        "pilot_storage_budgets_required",
    )
    services = document["services"]
    require(set(services) == set(BUDGETS), "exact_backend_roles_required")
    require(
        set(document["networks"]) == {"private-api"}
        and document["networks"]["private-api"].get("external") is True
        and document["networks"]["private-api"].get("name"),
        "existing_private_network_required",
    )
    mounts = {}
    for name, role in services.items():
        require(re.fullmatch(IMAGE, role["image"]), "immutable_image_required")
        require(
            role["user"] == "10001:10001"
            and role["read_only"] is True
            and role["cap_drop"] == ["ALL"]
            and role["security_opt"] == ["no-new-privileges:true"]
            and role["restart"] == "no"
            and role["pull_policy"] == "never",
            "manual_nonroot_lifecycle_required",
        )
        require(
            not any(
                role.get(key)
                for key in (
                    "ports",
                    "privileged",
                    "pid",
                    "ipc",
                    "devices",
                    "build",
                    "cap_add",
                    "volumes_from",
                    "env_file",
                    "secrets",
                    "configs",
                    "post_start",
                    "pre_stop",
                    "develop",
                    "provider",
                )
            ),
            "unsafe_runtime_extension",
        )
        require(role.get("labels") == {"traefik.enable": "false"}, "no_api_route")
        cpu, memory, pids = BUDGETS[name]
        require(
            float(role["cpus"]) == cpu
            and int(role["mem_limit"]) == int(role["memswap_limit"]) == memory
            and role["pids_limit"] == pids,
            "exact_role_budgets_required",
        )
        require(
            role["logging"]
            == {"driver": "json-file", "options": {"max-size": "10m", "max-file": "3"}}
            and role["stop_grace_period"] == "30s",
            "bounded_stop_and_logs_required",
        )
        expected = (
            {"/etc/caddy/Caddyfile", "/run/tls"}
            if name == "api-gateway"
            else {ROOT, "/var/lib/personal-assistant/catalog", CONFIG}
            | ({"/run/config/limits.json"} if name == "capacity-worker" else set())
        )
        volumes = role["volumes"]
        mounts[name] = {v["target"]: v for v in volumes}
        require(
            set(mounts[name]) == expected and len(volumes) == len(expected),
            "exact_mounts",
        )
        for mount in volumes:
            source = Path(mount["source"])
            require(
                mount["type"] == "bind"
                and mount["bind"]["create_host_path"] is False
                and bool(mount.get("read_only")) == (mount["target"] != ROOT)
                and source.is_absolute()
                and ".." not in source.parts,
                "explicit_private_mounts_required",
            )
        health = role["healthcheck"]
        require(
            health.get("disable") is not True
            and health["interval"] == "15s"
            and health["timeout"] == "5s"
            and health["retries"] == 3
            and health["start_period"] == "30s",
            "bounded_health_required",
        )
        expected_health = (
            ["CMD", "python", "/opt/gateway_health.py"]
            if name == "api-gateway"
            else [
                "CMD",
                "python",
                "-m",
                "scripts.deployment",
                "health",
                "--role",
                "api" if name == "api" else "worker",
                "--config",
                CONFIG,
            ]
        )
        require(health["test"] == expected_health, "canonical_health_required")
        require(
            role["profiles"]
            == [
                "c26-pilot-worker" if name == "capacity-worker" else "c26-pilot-control"
            ],
            "staged_activation_required",
        )
        expected_tmp = "64m" if name == "capacity-worker" else "32m"
        require(
            role["tmpfs"]
            == [f"/tmp:rw,noexec,nosuid,nodev,size={expected_tmp},mode=1777"],
            "bounded_tmpfs_required",
        )
    api, worker, gateway = (
        services[n] for n in ("api", "capacity-worker", "api-gateway")
    )
    require(api["image"] == worker["image"], "identical_backend_image_required")
    require(
        api["network_mode"] == "service:api-gateway" and not api.get("networks"),
        "loopback_namespace_required",
    )
    require(
        worker["network_mode"] == "none" and not worker.get("networks"),
        "offline_worker_required",
    )
    require(
        set(gateway["networks"]) == {"private-api"} and not gateway.get("network_mode"),
        "private_gateway_required",
    )
    require(
        not api.get("environment")
        and not worker.get("environment")
        and set(gateway["environment"]) == {"API_DNS"},
        "no_environment_secrets",
    )
    require(
        api["entrypoint"] == ["python", "-m", "scripts.deployment"]
        and api["command"] == ["api", "--config", CONFIG],
        "canonical_api_required",
    )
    require(
        worker["entrypoint"] == ["python", "-m", "scripts.cs50_worker"]
        and worker["command"]
        == ["--config", CONFIG, "--limits", "/run/config/limits.json"],
        "canonical_worker_required",
    )
    require(
        gateway["entrypoint"] == ["caddy"]
        and gateway["command"]
        == ["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"],
        "canonical_gateway_required",
    )
    for target in (ROOT, "/var/lib/personal-assistant/catalog", CONFIG):
        require(
            mounts["api"][target] == mounts["capacity-worker"][target],
            "shared_queue_and_settings_required",
        )
    sources = {Path(v["source"]) for group in mounts.values() for v in group.values()}
    require(
        len(sources) == 6
        and not any(a.is_relative_to(b) for a in sources for b in sources if a != b),
        "separate_host_sources_required",
    )
    return dict(
        status="offline_configuration_valid",
        execution_enabled=False,
        deployment_permitted=False,
        production_release="HOLD",
        live_gate_authority="not_implemented",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("compose", "controller", "limits"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = check(
            *(load(getattr(args, n)) for n in ("compose", "controller", "limits"))
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        RecursionError,
        OverflowError,
    ):
        print(
            json.dumps(
                dict(
                    status="refused",
                    deployment_permitted=False,
                    production_release="HOLD",
                )
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
