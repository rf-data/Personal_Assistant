"""Offline structural checks, explicitly distinct from native product validation."""

import json
import re
from pathlib import Path

import yaml

from src.core.pipeline_metrics import contract_document

DATA_MOUNTS = {
    "alert_manager": ("../monitoring/alertmanager/data", "/alertmanager"),
    "grafana": ("../monitoring/grafana/data", "/var/lib/grafana"),
    "portainer": ("../monitoring/portainer/data", "/data"),
    "prometheus": ("../monitoring/prometheus/data", "/prometheus"),
}
PROFILES = {
    "node-exporter": ["host"],
    "cAdvisor": ["containers"],
    "portainer": ["admin"],
}
IMAGES = {
    "alert_manager": "prom/alertmanager@sha256:${ALERTMANAGER_DIGEST:?Set approved 64 hex digest}",
    "node-exporter": "prom/node-exporter@sha256:${NODE_EXPORTER_DIGEST:?Set approved 64 hex digest}",
    "portainer": "portainer/portainer-ce@sha256:${PORTAINER_DIGEST:?Set approved 64 hex digest}",
    "grafana": "grafana/grafana:12.1.0",
    "prometheus": "prom/prometheus:v3.5.0",
    "cAdvisor": "gcr.io/cadvisor/cadvisor@sha256:3de2bd5203120b866d74a9b283b2ffb8ec382fbf9dc321814700c6ea6f44ec57",
}


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError("Duplicate YAML key")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def load_yaml(path):
    return yaml.load(Path(path).read_text(), Loader=UniqueLoader)


def mount_parts(mount):
    if isinstance(mount, str):
        source, target, *mode = mount.split(":")
        return source, target, mode == ["ro"]
    return mount["source"], mount["target"], mount.get("read_only", False)


def validate_overrides(environment):
    """Only nonsecret image identifiers/port numbers are inspected."""
    errors = []
    for prefix in ("ALERTMANAGER", "NODE_EXPORTER", "PORTAINER"):
        value = environment.get(prefix + "_DIGEST", "")
        if not re.fullmatch(r"[0-9a-f]{64}", value) or value == "0" * 64:
            errors.append(
                prefix + "_DIGEST requires an approved, non-placeholder SHA256"
            )
    for prefix in (
        "ALERTMANAGER",
        "NODE_EXPORTER",
        "PORTAINER",
        "CADVISOR",
        "GRAFANA",
        "PROMETHEUS",
    ):
        value = environment.get(prefix + "_PORT")
        if value is not None and (
            not value.isascii()
            or not value.isdecimal()
            or not 1024 <= int(value) <= 65535
        ):
            errors.append(prefix + "_PORT must be a nonprivileged numeric port")
    return errors


def validate_monitoring(root):
    root = Path(root)
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    compose = load_yaml(root / "docker/docker-compose.monitoring.yaml")
    services = compose["services"]
    check(set(services) == set(IMAGES), "Unexpected service set")
    for name, service in services.items():
        check(service["image"] == IMAGES.get(name), f"{name}: image approval changed")
        check(
            service.get("profiles", []) == PROFILES.get(name, []),
            f"{name}: unexpected profile",
        )
        check(service.get("read_only") is True, f"{name}: writable root filesystem")
        check(service.get("cap_drop") == ["ALL"], f"{name}: capabilities not dropped")
        check(
            service.get("security_opt") == ["no-new-privileges:true"],
            f"{name}: privilege escalation",
        )
        check(not service.get("privileged"), f"{name}: privileged container")
        check(service.get("networks") == ["monitoring"], f"{name}: unexpected network")
        check(service.get("restart") == "unless-stopped", f"{name}: restart policy")
        check(
            all(service.get(k) for k in ("pids_limit", "cpus", "mem_limit", "user")),
            f"{name}: missing resource/user limits",
        )
        check(
            all(p.startswith("127.0.0.1:") for p in service.get("ports", [])),
            f"{name}: public binding",
        )
        for mount in service.get("volumes", []):
            source, target, readonly = mount_parts(mount)
            writable_data = (
                name in DATA_MOUNTS and (source, target) == DATA_MOUNTS[name]
            )
            socket = name == "portainer" and source == target == "/var/run/docker.sock"
            check(writable_data or socket or readonly, f"{name}: unsafe writable mount")
            check("docker.sock" not in source or socket, f"{name}: unexpected socket")
            check(
                not source.startswith("/") or name in PROFILES,
                f"{name}: default host access",
            )
            if writable_data:
                check(
                    isinstance(mount, dict)
                    and mount.get("bind", {}).get("create_host_path") is False,
                    f"{name}: data paths must not be created automatically",
                )
        if name in DATA_MOUNTS:
            check(
                DATA_MOUNTS[name] in [mount_parts(m)[:2] for m in service["volumes"]],
                f"{name}: data path changed",
            )
        health = service.get("healthcheck", {})
        if name == "portainer":
            check(
                health == {"disable": True},
                "Portainer requires external readiness verification",
            )
        else:
            check(
                health.get("test", [None])[0] == "CMD"
                and health.get("timeout") == "5s"
                and health.get("retries") == 3,
                f"{name}: missing bounded readiness probe",
            )
    check(
        compose["networks"] == {"monitoring": {"internal": True}},
        "Monitoring network must be isolated",
    )
    env = services["grafana"]["environment"]
    check(env["GF_AUTH_ANONYMOUS_ENABLED"] == "false", "Anonymous Grafana enabled")
    check(
        env["GF_SECURITY_ADMIN_PASSWORD__FILE"]
        == "/run/secrets/grafana_admin_password",
        "Grafana requires external secret file",
    )
    check("GF_SECURITY_ADMIN_PASSWORD" not in env, "Inline Grafana password")

    prom = load_yaml(root / "monitoring/prometheus.yaml")
    check(
        prom["alerting"]["alertmanagers"][0]["static_configs"][0]["targets"]
        == ["alert_manager:9093"],
        "Incorrect Alertmanager DNS/port",
    )
    check(
        prom["rule_files"]
        == ["/etc/prometheus/rules/*.yaml", "/etc/prometheus/rules/*.yml"],
        "Incorrect rule paths",
    )
    jobs = {j["job_name"]: j for j in prom["scrape_configs"]}
    check(
        set(jobs)
        == {
            "prometheus",
            "alertmanager",
            "node_exporter",
            "cAdvisor",
            "personal_assistant_workers",
        },
        "Scrape jobs changed",
    )
    for name in ("node_exporter", "cAdvisor", "personal_assistant_workers"):
        check(
            "static_configs" not in jobs[name]
            and bool(jobs[name].get("file_sd_configs")),
            f"{name}: optional target must use discovery",
        )
    check(
        jobs["personal_assistant_workers"].get("sample_limit") == 5000
        and jobs["personal_assistant_workers"].get("target_limit") == 32,
        "Worker scrape limits",
    )
    rule_names = set()
    for path in sorted(
        [
            *(root / "monitoring/prometheus/rules").glob("*.yaml"),
            *(root / "monitoring/prometheus/rules").glob("*.yml"),
        ]
    ):
        for group in load_yaml(path)["groups"]:
            for rule in group["rules"]:
                name = rule.get("alert", rule.get("record"))
                check(name not in rule_names, "Duplicate rule name")
                rule_names.add(name)
                check(
                    isinstance(rule.get("expr"), str) and bool(rule["expr"]),
                    "Missing rule expression",
                )
    check(
        {
            "PrometheusTargetDown",
            "PipelineWorkerUnavailable",
            "PipelineMetricsMissing",
            "HostLowDisk",
            "PipelineHighFailureRate",
            "PipelineLongRunningJob",
        }
        <= rule_names,
        "Missing required alerts",
    )
    am = load_yaml(root / "monitoring/alertmanager/config/alertmanager.yaml")
    check(
        am["receivers"] == [{"name": "local-only"}]
        and am["route"]["receiver"] == "local-only",
        "Default receiver must send no notifications",
    )
    ds = load_yaml(
        root / "monitoring/grafana/provisioning/datasources/prometheus.yaml"
    )["datasources"][0]
    check(
        ds["uid"] == "pa-prometheus" and ds["url"] == "http://prometheus:9090",
        "Datasource mismatch",
    )
    provider = load_yaml(
        root / "monitoring/grafana/provisioning/dashboards/default.yaml"
    )["providers"][0]
    check(
        provider["disableDeletion"]
        and provider["options"]["path"] == "/etc/grafana/dashboards",
        "Unsafe dashboard provisioning",
    )
    uids = set()
    for path in sorted((root / "monitoring/grafana/dashboards").glob("*.json")):
        dashboard = json.loads(path.read_text())
        check(dashboard["uid"] not in uids, "Duplicate dashboard uid")
        uids.add(dashboard["uid"])
        for panel in dashboard["panels"]:
            for target in panel.get("targets", []):
                check(
                    panel["datasource"]["uid"] == ds["uid"],
                    "Unknown dashboard datasource",
                )
                check(
                    not re.search(r"vector\s*\(\s*0\s*\)", target["expr"]),
                    "Dashboard fabricates missing zeros",
                )
    check(uids == {"pa-system-v1", "pa-pipeline-v1"}, "Required dashboard missing")
    document = json.loads((root / "monitoring/pipeline-metrics.v1.json").read_text())
    # JSON encodes tuple labels as arrays.
    check(
        document == json.loads(json.dumps(contract_document())),
        "Metrics contract snapshot changed",
    )
    return errors
