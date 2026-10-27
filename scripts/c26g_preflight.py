"""Read-only checks of disabled staging inputs. Never authorizes a deployment.

Compose inputs must be normalized JSON, retained privately by the operator.
This tool does not render Compose, inspect a host, load credentials or open stores.
"""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from scripts.https_preflight import check as check_https
from scripts.https_preflight import require
from src.job_control.models import Settings

LIVE_BLOCKERS = (
    "image_build_and_registry_attestation",
    "host_mount_queue_writer_and_trigger_inventory",
    "tls_vpn_oidc_browser_and_revocation",
    "producer_build_identity_and_external_witness",
    "versioned_live_gate_and_mutating_driver",
    "content_review_search_runtime_wiring",
    "joint_restore_alarm_delivery_and_operator_approval",
)


def load(path):
    """Bounded JSON, with duplicate keys and nonfinite constants refused."""

    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, "duplicate_key")
            value[key] = item
        return value

    def nonfinite(_):
        raise ValueError("nonfinite_json")

    with Path(path).open("rb") as stream:
        data = stream.read(1024 * 1024 + 1)
    require(len(data) <= 1024 * 1024, "input_size")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=nonfinite)


def check(backend, ui, controller, *, origin, tls_router, http_router, middleware):
    """Validate the existing contracts; successful offline validation stays HOLD."""
    settings = Settings.model_validate(controller)
    require(
        getattr(settings, "deployment_gate_protocol", None) == "c26-gate-v2"
        and getattr(settings, "deployment_gate_required", False),
        "mandatory_v2_required",
    )
    require(
        not any(
            (
                settings.execution_enabled,
                settings.workflows_enabled,
                settings.pdf_enabled,
                settings.index_jobs_enabled,
                settings.import_jobs_enabled,
            )
        )
        and not settings.catalog
        and not settings.identities
        and (settings.max_parallel, settings.max_queued, settings.max_jobs) == (1, 1, 1)
        and not getattr(settings, "coordinator_test_required", False),
        "disabled_empty_staging_required",
    )
    require(str(settings.root) == "/app/runtime-state/c16", "runtime_root_required")
    services = backend["services"]
    require(set(services) == {"api-gateway", "api", "capacity-worker"}, "three_roles")
    require(
        services["api"]["image"] == services["capacity-worker"]["image"],
        "one_runtime_image",
    )
    require(
        services["api"].get("network_mode") == "service:api-gateway", "api_namespace"
    )
    require(
        services["capacity-worker"].get("network_mode") == "none", "isolated_executor"
    )
    require(
        services["api"].get("entrypoint") == ["python", "-m", "scripts.deployment"],
        "api_launcher",
    )
    require(
        services["api"].get("command")
        == [
            "api",
            "--config",
            "/app/configuration/c26-runtime/controller.json",
            "--port",
            "8016",
        ],
        "api_command",
    )
    require(
        services["capacity-worker"].get("entrypoint")
        == ["python", "-m", "scripts.cs50_worker"],
        "worker_launcher",
    )
    require(
        services["capacity-worker"].get("command")
        == [
            "--config",
            "/app/configuration/c26-runtime/controller.json",
            "--limits",
            "/app/configuration/c26-runtime/limits.json",
        ],
        "worker_command",
    )
    for name, role in services.items():
        require(
            re.fullmatch(r"[^\s]+@sha256:[a-f0-9]{64}", role["image"]),
            "immutable_image",
        )
        require(
            role.get("user") == "10001:10001" and role.get("read_only") is True,
            "private_roles",
        )
        require(
            role.get("pull_policy") == "never" and role.get("restart") == "no",
            "manual_staging_lifecycle",
        )
        require(
            "ALL" in role.get("cap_drop", [])
            and "no-new-privileges:true" in role.get("security_opt", []),
            "hardening",
        )
        require(
            not any(
                role.get(k)
                for k in (
                    "ports",
                    "privileged",
                    "pid",
                    "devices",
                    "build",
                    "cap_add",
                    "volumes_from",
                )
            ),
            "no_host_access",
        )
        require(
            role.get("healthcheck", {}).get("test")
            and not role["healthcheck"].get("disable"),
            "role_health",
        )
        require(
            role.get("profiles")
            == (
                ["c26-worker-approved"]
                if name == "capacity-worker"
                else ["c26-runtime-approved"]
            ),
            "explicit_profiles",
        )
        for volume in role.get("volumes", []):
            require(
                volume.get("type") == "bind"
                and Path(volume["source"]).is_absolute()
                and volume.get("bind", {}).get("create_host_path") is False,
                "existing_bind",
            )
            require(
                "docker.sock" not in volume["source"]
                and "docker.sock" not in volume["target"],
                "no_socket",
            )
        if name != "api-gateway":
            mounts = {v["target"]: v for v in role["volumes"]}
            require(
                "/app/runtime-state" in mounts
                and not mounts["/app/runtime-state"].get("read_only", False),
                "runtime_bind",
            )
            require(
                mounts["/app/configuration"].get("read_only") is True
                and mounts["/app/data"].get("read_only") is True,
                "readonly_inputs",
            )
    require(
        services["api"]["volumes"] == services["capacity-worker"]["volumes"],
        "identical_backend_mounts",
    )
    network = backend["networks"]["private-api"]
    require(
        network.get("external") is True and network.get("name"), "existing_api_network"
    )
    require(ui["networks"]["backend"]["name"] == network["name"], "paired_api_network")
    check_https(
        ui,
        origin=origin,
        profile="private-https",
        tls_router=tls_router,
        http_router=http_router,
        service="ui",
        middleware=middleware,
    )
    env = ui["services"]["ui"]["environment"]
    issuer = urlsplit(env.get("ADMIN_OIDC_ISSUER", ""))
    require(
        issuer.scheme == "https"
        and issuer.hostname
        and not issuer.username
        and not issuer.password
        and not issuer.query
        and not issuer.fragment,
        "https_issuer",
    )
    api = urlsplit(env["JOB_API_URL"])
    api_dns = services["api-gateway"]["environment"]["API_DNS"]
    require(
        api.hostname == api_dns
        and api.port == 8443
        and api_dns in services["api-gateway"]["networks"]["private-api"]["aliases"],
        "api_dns_binding",
    )
    return dict(
        status="offline_configuration_valid",
        production_release="HOLD",
        deployment_permitted=False,
        live_blockers=list(LIVE_BLOCKERS),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("backend-compose-json", "ui-compose-json", "controller"):
        parser.add_argument("--" + key, type=Path, required=True)
    for key in ("origin", "tls-router", "http-router", "middleware"):
        parser.add_argument("--" + key, required=True)
    args = parser.parse_args(argv)
    try:
        result = check(
            load(args.backend_compose_json),
            load(args.ui_compose_json),
            load(args.controller),
            origin=args.origin,
            tls_router=args.tls_router,
            http_router=args.http_router,
            middleware=args.middleware,
        )
    except (ValueError, TypeError, KeyError, OSError, AttributeError, RecursionError):
        print(
            json.dumps(
                dict(
                    status="refused",
                    production_release="HOLD",
                    deployment_permitted=False,
                )
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
