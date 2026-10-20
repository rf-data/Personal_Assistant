"""Offline audit of Coolify's rendered Compose JSON; never connects or deploys.

Input can contain environment metadata. Output contains fixed diagnostics only.
This checks the declared resource, not live proxy flags/firewalls/network members.
"""

import argparse
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


class Refused(ValueError):
    pass


def require(value, message):
    if not value:
        raise Refused(message)


def check(
    document, *, origin, profile, tls_router, http_router, service, middleware=None
):
    p = urlsplit(origin)
    require(
        p.scheme == "https"
        and p.hostname
        and p.netloc == p.hostname
        and not p.path
        and not p.query
        and not p.fragment,
        "exact_https_origin_required",
    )
    require(
        profile in {"private-https", "public-https"}, "explicit_access_profile_required"
    )
    services = document.get("services", {})
    require(set(services) == {"ui"}, "ui_only_no_backend_or_worker_creation")
    ui = services["ui"]
    require(
        re.fullmatch(r"[^\s]+@sha256:[a-f0-9]{64}", ui.get("image", "")),
        "immutable_ui_image_required",
    )
    require(
        not any(
            ui.get(k)
            for k in ("ports", "privileged", "pid", "network_mode", "devices", "build")
        ),
        "no_host_exposure_or_privileged_options",
    )
    require(
        ui.get("read_only") is True and ui.get("user") == "10001:10001",
        "nonroot_readonly_required",
    )
    require(
        "ALL" in ui.get("cap_drop", [])
        and "no-new-privileges:true" in ui.get("security_opt", []),
        "container_hardening_required",
    )
    require(
        ui.get("healthcheck", {}).get("test")
        == ["CMD", "python", "-m", "admin_ui_package.container_runtime", "health"]
        and not ui["healthcheck"].get("disable"),
        "canonical_health_required",
    )
    require(
        ui.get("restart") == "unless-stopped"
        and ui.get("pids_limit", 0) in range(1, 129),
        "bounded_lifecycle_required",
    )
    require(
        0 < float(ui.get("cpus", 0)) <= 1
        and 0 < int(ui.get("mem_limit", 0)) <= 805306368,
        "bounded_resources_required",
    )
    env = ui.get("environment", {})
    for key, expected in {
        "APP_ENV": "server",
        "JOB_BACKEND": "http",
        "JOB_API_MODE": "production",
        "ADMIN_AUTH_MODE": "oidc",
        "C22_PRODUCTION": "1",
        "C26_HTTPS": "1",
        "C26_UI_ORIGIN": origin,
        "FORWARDED_ALLOW_IPS": "",
    }.items():
        require(env.get(key) == expected, "mandatory_runtime_contract")
    api = urlsplit(env.get("JOB_API_URL", ""))
    require(
        api.scheme == "https"
        and api.hostname
        and not api.username
        and not api.password
        and not api.query
        and not api.fragment
        and api.path in ("", "/")
        and api.hostname != p.hostname,
        "private_verified_https_api_required",
    )
    require(env.get("C26_TRUSTED_PROXY_CIDRS"), "trusted_proxy_required")
    proxy_nets = [
        ipaddress.ip_network(v.strip())
        for v in env["C26_TRUSTED_PROXY_CIDRS"].split(",")
    ]
    require(all(n.prefixlen > 0 for n in proxy_nets), "universal_proxy_trust_refused")
    networks = document.get("networks", {})
    require(
        set(ui.get("networks", {})) == {"ingress", "backend"}
        and set(networks) == {"ingress", "backend"},
        "exact_network_contract_required",
    )
    require(
        all(n.get("external") and n.get("name") for n in networks.values()),
        "existing_external_networks_required",
    )
    require(
        networks["ingress"]["name"] != networks["backend"]["name"],
        "api_and_ingress_network_must_differ",
    )
    volumes = ui.get("volumes", [])
    require(
        len(volumes) == 3
        and {v.get("target") for v in volumes}
        == {
            "/run/secrets/c16",
            "/home/adminui/.streamlit/secrets.toml",
            "/run/ca/ca.crt",
        },
        "only_secret_and_ca_mounts_allowed",
    )
    for volume in volumes:
        require(
            volume.get("type") == "bind"
            and volume.get("read_only") is True
            and Path(volume.get("source", "")).is_absolute()
            and not volume.get("bind", {}).get("create_host_path", True)
            and "docker.sock" not in volume["source"],
            "existing_readonly_bind_required",
        )
    labels = ui.get("labels", {})
    require(isinstance(labels, dict), "normalized_compose_json_required")
    require(
        labels.get("traefik.docker.network") == networks["ingress"]["name"],
        "explicit_ingress_network_required",
    )
    prefix = "traefik.http.routers."
    routers = {k[len(prefix) :].split(".")[0] for k in labels if k.startswith(prefix)}
    require(
        routers == {tls_router, http_router} and tls_router != http_router,
        "exact_two_ui_routers_required",
    )
    host_rule = "Host(`" + p.hostname + "`)"
    for router in routers:
        require(
            labels.get(prefix + router + ".rule") == host_rule,
            "exact_host_rule_required",
        )
    tls = prefix + tls_router
    http = prefix + http_router
    require(
        str(labels.get(tls + ".tls")).lower() == "true"
        and labels.get(tls + ".service") == service,
        "tls_and_ui_service_required",
    )
    require(
        labels.get(tls + ".entrypoints")
        and labels.get(http + ".entrypoints")
        and labels[tls + ".entrypoints"] != labels[http + ".entrypoints"],
        "separate_http_https_entrypoints_required",
    )
    require(
        labels.get("traefik.http.services." + service + ".loadbalancer.server.port")
        == "8501",
        "streamlit_port_8501_required",
    )
    mids = labels.get(http + ".middlewares", "").split(",")
    require(
        any(
            labels.get(
                "traefik.http.middlewares."
                + m.removesuffix("@docker")
                + ".redirectscheme.scheme"
            )
            == "https"
            for m in mids
        ),
        "http_to_https_redirect_required",
    )
    require(
        not any(
            "basicauth" in k.lower()
            or "insecureskipverify" in k.lower()
            or "ipstrategy" in k.lower()
            for k in labels
        ),
        "unsafe_or_substitute_auth_refused",
    )
    if profile == "private-https":
        require(
            middleware
            and middleware in labels.get(tls + ".middlewares", "").split(","),
            "private_allowlist_must_be_attached_to_tls_router",
        )
        ranges = labels.get(
            "traefik.http.middlewares."
            + middleware.removesuffix("@docker")
            + ".ipallowlist.sourcerange",
            "",
        )
        require(ranges, "private_cidrs_required")
        for value in ranges.split(","):
            net = ipaddress.ip_network(value.strip(), strict=True)
            require(
                net.prefixlen > 0
                and net.is_private
                and not net.is_loopback
                and not net.is_link_local,
                "explicit_private_client_ranges_required",
            )
    return {
        "status": "https_deployment_prepared",
        "production_release": "production_release_blocked",
        "scope": "offline_rendered_configuration_only",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compose-json", type=Path, required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument(
        "--profile", choices=("private-https", "public-https"), required=True
    )
    parser.add_argument("--tls-router", required=True)
    parser.add_argument("--http-router", required=True)
    parser.add_argument("--service", required=True)
    parser.add_argument("--middleware")
    args = parser.parse_args()
    try:
        result = check(
            json.loads(args.compose_json.read_bytes()),
            origin=args.origin,
            profile=args.profile,
            tls_router=args.tls_router,
            http_router=args.http_router,
            service=args.service,
            middleware=args.middleware,
        )
    except (ValueError, TypeError, KeyError, OSError):
        print(json.dumps({"status": "production_release_blocked", "check": "refused"}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
