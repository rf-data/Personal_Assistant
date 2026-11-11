"""Deterministic offline fixtures; no real host, Docker or Coolify endpoints."""

import copy
import hashlib
import json

import httpx
import pytest
from pydantic import ValidationError

from src.job_control.coolify_observer import (
    HostCollector,
    ObserverBinding,
    OperationPlan,
    RuntimeScope,
    bind_gate_plan,
    check_runtime_pair,
    observe_runtime,
)
from src.job_control.coolify_readiness import CoolifyReadClient, ReadScope, Refused
from src.job_control.models import canonical

NOW = 1000.0
SHA = "a" * 40
BACKEND = "registry.invalid/backend@sha256:" + "b" * 64
GATEWAY = "registry.invalid/gateway@sha256:" + "c" * 64


def fixture():
    mounts = [
        dict(
            source="/srv/runtime",
            destination="/app/runtime-state",
            read_only=False,
            device=1,
            inode=2,
        )
    ]
    gateway_mounts = [
        dict(
            source="/srv/Caddyfile",
            destination="/etc/caddy/Caddyfile",
            read_only=True,
            device=1,
            inode=3,
        )
    ]
    roles = [
        dict(
            role=role,
            service=role,
            revision=SHA,
            image=GATEWAY if i == 1 else BACKEND,
            image_id="sha256:" + ("d" if i == 1 else "e") * 64,
            build_receipt_sha256=("f" if i == 1 else "1") * 64,
            command_sha256=str(i + 2) * 64,
            health_contract_sha256="5" * 64,
            readiness_contract_sha256="6" * 64,
            mounts=gateway_mounts if i == 1 else mounts,
        )
        for i, role in enumerate(("api", "api-gateway", "capacity-worker"))
    ]
    scope = RuntimeScope(
        application_uuid="backend",
        protected_ui_uuid="ui",
        server_uuid="server",
        environment_uuid="env",
        repository="rf-data/Personal_Assistant",
        branch="master",
        compose_location="/deployment/coolify.runtime-bootstrap.compose.yaml",
        compose_project="backend_project",
        compose_sha256="1" * 64,
        settings_sha256="2" * 64,
        persistence_sha256="3" * 64,
        protected_resources_sha256="4" * 64,
        caddy_sha256="5" * 64,
        tls_binding_sha256="6" * 64,
        trigger_policy_sha256="7" * 64,
        allowed_trigger_actors=("exclusive_coordinator",),
        private_network_id="8" * 64,
        private_network_name="private",
        jobroot=dict(
            source="/srv/runtime/c16",
            destination="/app/runtime-state/c16",
            read_only=False,
            device=1,
            inode=4,
        ),
        roles=roles,
    )
    binding = ObserverBinding(
        scope=scope,
        phase="current",
        deployment_uuid="deployment",
        host_id="host",
        adapter_id="synthetic",
    )
    plan = OperationPlan(gate_plan_sha256="9" * 64, current=scope, target=scope)
    containers, images, members = {}, {}, []
    for i, role in enumerate(scope.roles):
        cid = str(i + 1) * 64
        members.append(
            dict(
                container_id=cid,
                application_uuid="backend",
                compose_project="backend_project",
                writable_sources=["/srv/runtime"] if i != 1 else [],
            )
        )
        containers[cid] = dict(
            container_id=cid,
            application_uuid="backend",
            compose_project="backend_project",
            service=role.service,
            role=role.role,
            image_id=role.image_id,
            command_sha256=role.command_sha256,
            settings_sha256=scope.settings_sha256 if i != 1 else None,
            mounts=[m.model_dump() for m in role.mounts],
            jobroot=scope.jobroot.model_dump() if i != 1 else None,
            running=True,
            process_verified=True,
            healthy=True,
            ready=True,
            health_contract_sha256=role.health_contract_sha256,
            readiness_contract_sha256=role.readiness_contract_sha256,
            network_mode="container:" + "2" * 64
            if i == 0
            else "private"
            if i == 1
            else "none",
            network_namespace="shared" if i != 2 else "worker",
            network_ids=["8" * 64] if i == 1 else [],
            host_ports=[],
            heartbeat_at=NOW if i == 2 else None,
        )
        images[role.image_id] = dict(
            image_id=role.image_id,
            repo_digests=[role.image],
            repository=scope.repository,
            revision=SHA,
            provenance="verified_build_receipt",
            build_receipt_sha256=role.build_receipt_sha256,
        )
    boundary = {
        name: getattr(scope, name)
        for name in (
            "server_uuid",
            "environment_uuid",
            "compose_sha256",
            "settings_sha256",
            "persistence_sha256",
            "protected_resources_sha256",
            "caddy_sha256",
            "tls_binding_sha256",
            "trigger_policy_sha256",
            "private_network_id",
        )
    }
    boundary.update(
        trigger_inventory_complete=True,
        trigger_actors=["exclusive_coordinator"],
        private_network_internal=True,
        tls_verified=True,
        external_intake_fenced=True,
        external_jobs_idle=True,
        writer_inventory_complete=True,
        jobroot_writer_ids=["1" * 64, "3" * 64],
    )
    app = dict(
        uuid="backend",
        build_pack="dockercompose",
        git_repository=scope.repository,
        git_branch="master",
        git_commit_sha=SHA,
        base_directory="/",
        docker_compose_location=scope.compose_location,
        settings=dict(
            is_auto_deploy_enabled=False, is_preview_deployments_enabled=False
        ),
    )
    deployment = dict(
        deployment_uuid="deployment", commit=SHA, status="finished", pull_request_id=0
    )
    raw = dict(
        inventory=dict(complete=True, members=members),
        containers=containers,
        images=images,
        boundary=boundary,
        application=app,
        deployment=deployment,
    )
    return binding, plan, raw


class Adapter:
    def __init__(self, raw):
        self.raw, self.calls = raw, []

    def query(self, query, identity):
        self.calls.append((query, identity))
        if query == "container":
            return json.dumps(self.raw["containers"][identity]).encode()
        if query == "image":
            return json.dumps(self.raw["images"][identity]).encode()
        assert (query, identity) in {("inventory", None), ("boundary", "backend")}
        return json.dumps(self.raw[query]).encode()


def observe(binding, plan, raw, *, adapter=None, now=NOW):
    adapter = adapter or Adapter(raw)
    collector = HostCollector(
        adapter=adapter, host_id="host", adapter_id="synthetic", clock=lambda: NOW
    )

    def handler(request):
        assert request.method == "GET"
        if request.url.path == "/api/v1/applications/backend":
            return httpx.Response(200, json=raw["application"])
        assert request.url.path == "/api/v1/deployments/applications/backend"
        return httpx.Response(200, json={"deployments": [raw["deployment"]]})

    client = CoolifyReadClient(
        "https://coolify.invalid",
        ReadScope(application_uuid="backend", deployment_uuid="deployment"),
        transport=httpx.MockTransport(handler),
    )
    try:
        return observe_runtime(
            binding, plan, collector=collector, client=client, now=now
        )
    finally:
        client.close()


def test_offline_success_is_reproducible_and_never_authorizes():
    binding, plan, raw = fixture()
    adapter = Adapter(raw)
    report = observe(binding, plan, raw, adapter=adapter)
    assert report.status == "verified_offline", report
    assert report == observe(binding, plan, raw)
    assert not report.deployment_permitted and report.production_release == "blocked"
    assert not hasattr(report, "healthy")
    assert len(adapter.calls) == 7
    assert {query for query, _ in adapter.calls} == {
        "inventory",
        "container",
        "image",
        "boundary",
    }
    assert check_runtime_pair(report, report, now=NOW) == report


@pytest.mark.parametrize(
    "path,value",
    [
        (("application", "uuid"), "other"),
        (("application", "git_commit_sha"), "f" * 40),
        (("application", "settings", "is_preview_deployments_enabled"), None),
        (("boundary", "caddy_sha256"), "0" * 64),
        (
            ("boundary", "trigger_actors"),
            ["exclusive_coordinator", "unknown_api_actor"],
        ),
        (("boundary", "trigger_inventory_complete"), None),
        (("boundary", "writer_inventory_complete"), None),
        (("boundary", "jobroot_writer_ids"), ["3" * 64, "4" * 64]),
        (("boundary", "private_network_internal"), False),
        (("boundary", "tls_verified"), None),
        (("boundary", "external_jobs_idle"), False),
        (("boundary", "persistence_sha256"), "0" * 64),
        (("inventory", "complete"), None),
        (("containers", "1" * 64, "image_id"), "sha256:" + "0" * 64),
        (("containers", "1" * 64, "application_uuid"), "foreign"),
        (("containers", "1" * 64, "service"), "sleep_placeholder"),
        (("containers", "1" * 64, "command_sha256"), None),
        (("containers", "1" * 64, "settings_sha256"), None),
        (("containers", "3" * 64, "settings_sha256"), "0" * 64),
        (("containers", "1" * 64, "process_verified"), None),
        (("containers", "1" * 64, "jobroot", "inode"), 999),
        (("containers", "3" * 64, "jobroot", "source"), "/srv/other/c16"),
        (("containers", "1" * 64, "mounts", 0, "source"), "/srv/other"),
        (("containers", "1" * 64, "mounts", 0, "destination"), "/app/other"),
        (("containers", "1" * 64, "network_namespace"), "other_namespace"),
        (("containers", "2" * 64, "network_ids"), []),
        (("containers", "1" * 64, "host_ports"), [8016]),
        (("containers", "3" * 64, "heartbeat_at"), None),
        (("containers", "3" * 64, "heartbeat_at"), NOW - 10),
        (("containers", "1" * 64, "healthy"), False),
        (("containers", "2" * 64, "healthy"), False),
        (("containers", "3" * 64, "ready"), None),
        (("containers", "2" * 64, "readiness_contract_sha256"), "0" * 64),
        (
            ("images", "sha256:" + "d" * 64, "repo_digests"),
            ["registry.invalid/gateway@sha256:" + "0" * 64],
        ),
        (("images", "sha256:" + "e" * 64, "repo_digests"), []),
        (("images", "sha256:" + "e" * 64, "revision"), "f" * 40),
        (("images", "sha256:" + "e" * 64, "provenance"), "label_only"),
        (("images", "sha256:" + "e" * 64, "build_receipt_sha256"), None),
    ],
)
def test_negative_evidence_is_no_go(path, value):
    binding, plan, raw = fixture()
    target = raw
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    report = observe(binding, plan, raw)
    assert (
        report.status == "NO-GO"
        and report.unverified
        and not report.deployment_permitted
    )


@pytest.mark.parametrize(
    "kind",
    [
        "extra",
        "second_worker",
        "foreign_writer",
        "duplicate_member",
        "contradictory_container",
        "missing_image",
    ],
)
def test_incomplete_or_contradictory_collectors_refused(kind):
    binding, plan, raw = fixture()
    member = copy.deepcopy(raw["inventory"]["members"][2])
    if kind in {"extra", "second_worker", "foreign_writer"}:
        member["container_id"] = "4" * 64
        if kind == "foreign_writer":
            member.update(application_uuid="foreign", compose_project="foreign")
        raw["inventory"]["members"].append(member)
    elif kind == "duplicate_member":
        raw["inventory"]["members"].append(member)
    elif kind == "contradictory_container":
        raw["containers"]["1" * 64]["container_id"] = "4" * 64
    else:
        del raw["images"]["sha256:" + "e" * 64]
    assert observe(binding, plan, raw).status == "NO-GO"


@pytest.mark.parametrize(
    "kind", ["oversized", "invalid_json", "duplicate_key", "nested_secrets", "error"]
)
def test_adapter_errors_and_secrets_are_redacted(kind):
    binding, plan, raw = fixture()

    class Broken(Adapter):
        def query(self, query, identity):
            if kind == "oversized":
                return b"DO_NOT_ECHO" * 7000
            if kind == "invalid_json":
                return b"DO_NOT_ECHO"
            if kind == "duplicate_key":
                return b'{"complete":true,"complete":"DO_NOT_ECHO"}'
            if kind == "error":
                raise Refused("DO_NOT_ECHO")
            raw["inventory"]["members"][0]["Env"] = ["DO_NOT_ECHO"]
            return super().query(query, identity)

    report = observe(binding, plan, raw, adapter=Broken(raw))
    assert report.status == "NO-GO" and "DO_NOT_ECHO" not in report.model_dump_json()


def test_top_level_unrequested_data_is_not_returned():
    binding, plan, raw = fixture()
    raw["inventory"]["Env"] = ["DO_NOT_ECHO"]
    collector = HostCollector(
        adapter=Adapter(raw), host_id="host", adapter_id="synthetic", clock=lambda: NOW
    )
    evidence = collector.collect(binding)
    assert "DO_NOT_ECHO" not in evidence.model_dump_json()
    assert observe(binding, plan, raw).status == "verified_offline"


@pytest.mark.parametrize(
    "kind", ["stale", "future", "different_host", "interrupted_pair", "namespace_drift"]
)
def test_freshness_provenance_and_drift(kind):
    binding, plan, raw = fixture()
    first = observe(binding, plan, raw)
    if kind in {"stale", "future"}:
        second = observe(
            binding, plan, raw, now=NOW + 31 if kind == "stale" else NOW - 1
        )
    elif kind == "different_host":
        binding = binding.model_copy(update={"host_id": "other"})
        second = observe(binding, plan, raw)
    elif kind == "interrupted_pair":
        second = None
    else:
        for cid in ("1" * 64, "2" * 64):
            raw["containers"][cid]["network_namespace"] = "replacement_namespace"
        second = observe(binding, plan, raw)
        assert second.status == "verified_offline"
    with pytest.raises(Refused):
        check_runtime_pair(first, second, now=NOW)


def test_operation_hash_is_canonical_and_binds_gateway_configuration_and_both_states():
    binding, plan, _ = fixture()
    assert (
        plan.runtime_scope_sha256
        == hashlib.sha256(canonical(plan.model_dump(mode="json"))).hexdigest()
    )
    reversed_keys = dict(reversed(list(plan.model_dump(mode="json").items())))
    assert (
        OperationPlan.model_validate(reversed_keys).runtime_scope_sha256
        == plan.runtime_scope_sha256
    )
    for phase in ("current", "target"):
        for path in (
            ("caddy_sha256",),
            ("compose_sha256",),
            ("trigger_policy_sha256",),
            ("roles", 1, "image"),
            ("roles", 0, "health_contract_sha256"),
        ):
            changed = plan.model_dump(mode="json")
            node = changed[phase]
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = (
                "registry.invalid/gateway@sha256:" + "0" * 64
                if path[-1] == "image"
                else "0" * 64
            )
            assert (
                OperationPlan.model_validate(changed).runtime_scope_sha256
                != plan.runtime_scope_sha256
            )
    assert (
        "deployment_uuid" not in plan.model_dump_json()
        and "container_id" not in plan.model_dump_json()
    )
    bad = plan.model_dump(mode="json")
    bad["current"]["unexpected_secret"] = "DO_NOT_ECHO"
    with pytest.raises(ValidationError):
        OperationPlan.model_validate(bad)


def test_gate_envelope_is_not_silently_accepted_by_v1_gate():
    gate = pytest.importorskip(
        "src.job_control.deployment_gate", reason="#148 integration dependency"
    )
    binding, _, _ = fixture()
    scope = binding.scope
    legacy = gate.Plan(
        resource_id=scope.application_uuid,
        role="api",
        current_sha=SHA,
        target_sha=SHA,
        current_image=BACKEND,
        target_image=BACKEND,
        settings_sha256=scope.settings_sha256,
        persistence_sha256=scope.persistence_sha256,
        protected_resources_sha256=scope.protected_resources_sha256,
    )
    envelope = bind_gate_plan(legacy, scope, scope)
    assert envelope.gate_plan_sha256 == legacy.digest
    with pytest.raises(ValidationError):
        gate.Plan.model_validate(
            {
                **legacy.model_dump(),
                "runtime_scope_sha256": envelope.runtime_scope_sha256,
            }
        )
    with pytest.raises(Refused):
        bind_gate_plan(legacy.model_copy(update={"resource_id": "other"}), scope, scope)


def test_pair_binds_phase_deployment_and_host_receipt():
    binding, plan, raw = fixture()
    first = observe(binding, plan, raw)
    # Same scope and instances, but another late deployment receipt.
    second = first.model_copy(update={"binding_sha256": "0" * 64})
    with pytest.raises(Refused):
        check_runtime_pair(first, second, now=NOW)


@pytest.mark.parametrize(
    "field,value",
    [
        ("private_network_internal", False),
        ("published_host_ports", [8016]),
        ("schema_version", 2),
    ],
)
def test_scope_cannot_authorize_unsafe_topology(field, value):
    binding, _, _ = fixture()
    data = binding.scope.model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        RuntimeScope.model_validate(data)


def test_selected_inventory_writes_must_match_actual_mounts():
    binding, plan, raw = fixture()
    raw["inventory"]["members"][0]["writable_sources"] = []
    assert observe(binding, plan, raw).status == "NO-GO"


def test_bound_operation_cannot_observe_another_scope():
    binding, plan, raw = fixture()
    changed = binding.scope.model_dump(mode="json")
    changed["caddy_sha256"] = "0" * 64
    binding = binding.model_copy(update={"scope": RuntimeScope.model_validate(changed)})
    assert observe(binding, plan, raw).reasons == ("operation_binding_mismatch",)


def test_collector_query_allowlist_refuses_before_adapter():
    from src.job_control.coolify_observer import Inventory

    _, _, raw = fixture()
    adapter = Adapter(raw)
    collector = HostCollector(
        adapter=adapter, host_id="host", adapter_id="synthetic", clock=lambda: NOW
    )
    for query, identity in [
        ("deploy", "backend"),
        ("container", "$(id)"),
        ("inventory", "foreign"),
        ("image", "latest"),
    ]:
        with pytest.raises(Refused):
            collector._query(query, identity, Inventory)
    assert adapter.calls == []


def test_collector_rejects_credentials_disguised_as_repository_metadata():
    binding, plan, raw = fixture()
    raw["images"]["sha256:" + "e" * 64]["repository"] = (
        "https://DO_NOT_ECHO@github.com/owner/repo"
    )
    collector = HostCollector(
        adapter=Adapter(raw), host_id="host", adapter_id="synthetic", clock=lambda: NOW
    )
    with pytest.raises(Refused) as error:
        collector.collect(binding)
    assert "DO_NOT_ECHO" not in str(error.value)
    assert "DO_NOT_ECHO" not in observe(binding, plan, raw).model_dump_json()
