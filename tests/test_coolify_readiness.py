"""Synthetic replay only. Never contacts Coolify, Docker, queues or host paths."""

import httpx
import pytest
from pydantic import ValidationError

from src.job_control.coolify_readiness import (
    CoolifyReadClient,
    ReadScope,
    Refused,
    RoleBinding,
    RuntimeBinding,
    RuntimeRead,
    check_observation_pair,
    check_snapshot,
)

NOW = 1000.0
SHA = "a" * 40
IMAGE = "registry.invalid/backend@sha256:" + "b" * 64
GATEWAY = "registry.invalid/gateway@sha256:" + "c" * 64


def fixture_pair():
    roles = tuple(
        RoleBinding(
            role=role,
            revision=SHA,
            image=GATEWAY if role == "api-gateway" else IMAGE,
            image_id="sha256:" + ("d" if role == "api-gateway" else "e") * 64,
            mounts_sha256=("f" if role == "api-gateway" else "1") * 64,
        )
        for role in ("api", "api-gateway", "capacity-worker")
    )
    binding = RuntimeBinding(
        application_uuid="synthetic_backend",
        protected_ui_uuid="synthetic_ui",
        deployment_uuid="synthetic_deploy",
        server_uuid="synthetic_server",
        environment_uuid="synthetic_environment",
        repository="rf-data/Personal_Assistant",
        branch="synthetic_pinned_branch",
        base_directory="/",
        compose_location="/deployment/coolify.runtime-bootstrap.compose.yaml",
        compose_project="synthetic_project",
        git_commit_sha=SHA,
        settings_sha256="2" * 64,
        persistence_sha256="3" * 64,
        protected_resources_sha256="4" * 64,
        trigger_policy_sha256="5" * 64,
        private_network_id="6" * 64,
        private_network_name="private",
        tls_binding_sha256="7" * 64,
        roles=roles,
    )
    app = dict(
        uuid=binding.application_uuid,
        build_pack="dockercompose",
        git_repository=binding.repository,
        git_branch=binding.branch,
        git_commit_sha=SHA,
        base_directory="/",
        docker_compose_location=binding.compose_location,
        auto_deploy_enabled=False,
        preview_deployments_enabled=False,
    )
    role_reads = []
    for i, role in enumerate(roles):
        data = role.model_dump(mode="json")
        data.update(
            container_id=str(i + 1) * 64,
            network_mode="container:" + "2" * 64
            if i == 0
            else "private"
            if i == 1
            else "none",
            network_namespace="shared_gateway" if i < 2 else "isolated_worker",
            healthy=True,
            ready=True,
            heartbeat_at=NOW if i == 2 else None,
        )
        role_reads.append(data)
    data = {
        name: getattr(binding, name)
        for name in (
            "server_uuid",
            "environment_uuid",
            "compose_project",
            "settings_sha256",
            "persistence_sha256",
            "protected_resources_sha256",
            "trigger_policy_sha256",
            "private_network_id",
            "tls_binding_sha256",
        )
    }
    data.update(
        inventory_complete=True,
        resource_container_ids=[str(i + 1) * 64 for i in range(3)],
        application=app,
        deployment=dict(
            deployment_uuid="synthetic_deploy",
            commit=SHA,
            status="finished",
            pull_request_id=0,
        ),
        binding_sha256=binding.digest,
        tls_verified=True,
        additional_triggers_controlled=True,
        external_intake_fenced=True,
        external_jobs_idle=True,
        observed_at=NOW,
        roles=role_reads,
    )
    return binding, RuntimeRead.model_validate(data)


def altered(reading, path, value):
    data = reading.model_dump(mode="json")
    current = data
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value
    return RuntimeRead.model_validate(data)


def test_consistent_replay_is_never_gate_permission():
    binding, reading = fixture_pair()
    report = check_snapshot(binding, reading, now=NOW)
    assert report.replay_consistent is True
    assert (
        report.deployment_permitted is False and report.production_release == "blocked"
    )
    assert not hasattr(CoolifyReadClient, "deploy")
    assert not hasattr(CoolifyReadClient, "rollback")
    assert not hasattr(report, "healthy")  # deliberately not a Gate Observation


@pytest.mark.parametrize(
    "path,value",
    [
        (("application", "uuid"), "unknown_application"),
        (("application", "build_pack"), "dockerfile"),
        (("application", "git_branch"), "moving_other_branch"),
        (("application", "git_commit_sha"), "HEAD"),
        (("application", "auto_deploy_enabled"), True),
        (("application", "preview_deployments_enabled"), None),
        (("application", "docker_compose_location"), "/other.yaml"),
        (("deployment", "deployment_uuid"), "different_deployment"),
        (("deployment", "commit"), "b" * 40),
        (("deployment", "status"), "in_progress"),
        (("deployment", "pull_request_id"), 1),
        (("binding_sha256",), "0" * 64),
        (("compose_project",), "foreign_project"),
        (("server_uuid",), "other_server"),
        (("environment_uuid",), "other_environment"),
        (("persistence_sha256",), "0" * 64),
        (("protected_resources_sha256",), "0" * 64),
        (("private_network_id",), "0" * 64),
        (("tls_binding_sha256",), "0" * 64),
        (("trigger_policy_sha256",), "0" * 64),
        (("tls_verified",), False),
        (("additional_triggers_controlled",), False),
        (("external_jobs_idle",), False),
        (("inventory_complete",), False),
        (("resource_container_ids",), ["1" * 64, "2" * 64, "3" * 64, "4" * 64]),
        (("roles", 1, "network_mode"), "coolify"),
        (("external_intake_fenced",), False),
        (("observed_at",), NOW - 31),
        (("observed_at",), NOW + 1),
        (("roles", 0, "healthy"), False),
        (("roles", 1, "healthy"), False),
        (("roles", 2, "ready"), False),
        (("roles", 0, "mounts_sha256"), "0" * 64),
        (("roles", 2, "image"), "registry.invalid/backend@sha256:" + "9" * 64),
        (("roles", 2, "image_id"), "sha256:" + "b" * 64),
        (("roles", 2, "revision"), "b" * 40),
        (("roles", 0, "network_namespace"), "wrong_namespace"),
        (("roles", 0, "network_mode"), "coolify"),
        (("roles", 2, "network_mode"), "coolify"),
        (("roles", 2, "heartbeat_at"), None),
        (("roles", 2, "heartbeat_at"), NOW - 10),
    ],
)
def test_negative_runtime_evidence_fails_closed(path, value):
    binding, reading = fixture_pair()
    with pytest.raises(Refused):
        check_snapshot(binding, altered(reading, path, value), now=NOW)


@pytest.mark.parametrize(
    "kind", ["additional_container", "second_worker", "duplicate_id"]
)
def test_unexpected_instances_refused(kind):
    binding, reading = fixture_pair()
    data = reading.model_dump(mode="json")
    if kind == "additional_container":
        data["roles"].append(data["roles"][2].copy())
    elif kind == "second_worker":
        data["roles"][0]["role"] = "capacity-worker"
    else:
        data["roles"][0]["container_id"] = data["roles"][2]["container_id"]
    with pytest.raises((Refused, ValidationError)):
        check_snapshot(binding, RuntimeRead.model_validate(data), now=NOW)


def test_interrupted_pair_cannot_reuse_previous_success():
    binding, first = fixture_pair()
    check_observation_pair(binding, first, first, now=NOW)
    with pytest.raises(Refused):
        check_observation_pair(binding, first, None, now=NOW)
    with pytest.raises(Refused):
        check_observation_pair(
            binding,
            first,
            altered(first, ("roles", 2, "container_id"), "9" * 64),
            now=NOW,
        )
    with pytest.raises(Refused):
        check_observation_pair(
            binding, first, altered(first, ("persistence_sha256",), "0" * 64), now=NOW
        )
    with pytest.raises(Refused):
        check_observation_pair(binding, first, first, now=NOW + 31)
    assert (
        check_observation_pair(binding, first, first, now=NOW).deployment_permitted
        is False
    )


def raw_application():
    _, reading = fixture_pair()
    raw = reading.application.model_dump(mode="json")
    raw.pop("auto_deploy_enabled")
    raw.pop("preview_deployments_enabled")
    raw["settings"] = dict(
        is_auto_deploy_enabled=False, is_preview_deployments_enabled=False
    )
    raw.update(
        manual_webhook_secret_github="DO_NOT_ECHO",
        docker_compose_raw="DO_NOT_ECHO",
        envs=["DO_NOT_ECHO"],
    )
    return raw


def read_client(handler, **scope_updates):
    scope = ReadScope(
        application_uuid="synthetic_backend",
        deployment_uuid="synthetic_deploy",
        **scope_updates,
    )
    return CoolifyReadClient(
        "https://coolify.example.invalid", scope, transport=httpx.MockTransport(handler)
    )


def test_client_uses_exact_get_allowlist_and_drops_sensitive_fields():
    calls = []

    def handler(request):
        calls.append((request.method, str(request.url)))
        if request.url.path == "/api/v1/applications/synthetic_backend":
            return httpx.Response(200, json=raw_application())
        assert request.url.path == "/api/v1/deployments/applications/synthetic_backend"
        assert request.url.query == b"skip=0&take=16"
        return httpx.Response(
            200,
            json={
                "count": 1,
                "deployments": [
                    dict(
                        deployment_uuid="synthetic_deploy",
                        commit=SHA,
                        status="finished",
                        pull_request_id=0,
                        logs="DO_NOT_ECHO",
                        configuration_snapshot={"secret": "DO_NOT_ECHO"},
                    )
                ],
            },
        )

    client = read_client(handler)
    try:
        assert "DO_NOT_ECHO" not in client.application().model_dump_json()
        assert "DO_NOT_ECHO" not in client.deployment().model_dump_json()
        assert all(method == "GET" for method, _ in calls) and len(calls) == 2
    finally:
        client.close()


@pytest.mark.parametrize(
    "origin",
    [
        "http://coolify.example.invalid",
        "https://user:secret@example.invalid",
        "https://example.invalid/deploy",
        "https://example.invalid?uuid=x",
    ],
)
def test_untrusted_origins_refused_before_any_request(origin):
    with pytest.raises(Refused):
        CoolifyReadClient(
            origin,
            ReadScope(application_uuid="fixture", deployment_uuid="fixture"),
            transport=httpx.MockTransport(lambda _: pytest.fail("No request allowed")),
        )


@pytest.mark.parametrize(
    "kind",
    [
        "redirect",
        "error",
        "oversized",
        "duplicate_key",
        "wrong_uuid",
        "unexpected_build_pack",
        "compressed",
        "credential_repository",
        "missing_flags",
        "missing_deployment",
        "duplicate_deployment",
        "interrupted",
    ],
)
def test_client_errors_never_echo_responses_or_follow_redirects(kind):
    calls = []

    def handler(request):
        calls.append(request)
        if kind == "redirect":
            return httpx.Response(
                302, headers={"Location": "https://foreign.invalid/deploy"}
            )
        if kind == "error":
            return httpx.Response(403, text="DO_NOT_ECHO")
        if kind == "oversized":
            return httpx.Response(200, content=b" " * 131073)
        if kind == "duplicate_key":
            return httpx.Response(
                200, content=b'{"uuid":"fixture","uuid":"DO_NOT_ECHO"}'
            )
        if kind == "interrupted":
            raise httpx.ReadTimeout("DO_NOT_ECHO")
        raw = raw_application()
        if kind == "compressed":
            return httpx.Response(
                200, headers={"content-encoding": "br"}, content=b"DO_NOT_ECHO"
            )
        if kind == "unexpected_build_pack":
            raw["build_pack"] = "nixpacks"
        if kind == "wrong_uuid":
            raw["uuid"] = "foreign"
        if kind == "credential_repository":
            raw["git_repository"] = (
                "https://DO_NOT_ECHO@github.com/rf-data/Personal_Assistant"
            )
        if kind == "missing_flags":
            raw.pop("settings")
        if kind in {"missing_deployment", "duplicate_deployment"}:
            item = dict(
                deployment_uuid="synthetic_deploy",
                commit=SHA,
                status="finished",
                pull_request_id=0,
            )
            return httpx.Response(
                200,
                json={
                    "deployments": [] if kind == "missing_deployment" else [item, item]
                },
            )
        return httpx.Response(200, json=raw)

    client = read_client(handler)
    try:
        if kind == "missing_flags":
            assert client.application().auto_deploy_enabled is None
        else:
            with pytest.raises(Refused) as error:
                client.deployment() if kind.endswith(
                    "deployment"
                ) else client.application()
            assert "DO_NOT_ECHO" not in str(error.value)
        assert len(calls) == 1
    finally:
        client.close()


def test_binding_rejects_unknown_scope_or_nonimmutable_image():
    binding, _ = fixture_pair()
    data = binding.model_dump(mode="json")
    data["application_uuid"] = ""
    with pytest.raises(ValidationError):
        RuntimeBinding.model_validate(data)
    data = binding.model_dump(mode="json")
    data["roles"][0]["image"] = "registry.invalid/backend:latest"
    with pytest.raises(ValidationError):
        RuntimeBinding.model_validate(data)


def test_full_role_binding_cannot_be_replaced_by_v1_backend_anchor():
    binding, _ = fixture_pair()
    changed = binding.model_dump(mode="json")
    changed["roles"][1]["image"] = "registry.invalid/gateway@sha256:" + "0" * 64
    other = RuntimeBinding.model_validate(changed)
    assert other.git_commit_sha == binding.git_commit_sha
    assert other.roles[0] == binding.roles[0]
    assert other.digest != binding.digest  # v1 Plan backend fields cannot express this


def test_arbitrary_get_and_unknown_uuid_refused_before_transport():
    client = read_client(lambda _: pytest.fail("No request allowed"))
    try:
        for path in (
            "/api/v1/deploy?uuid=fixture",
            "/api/v1/applications/foreign",
            "https://foreign.invalid/api/v1/deploy",
        ):
            with pytest.raises(Refused):
                client._read(path)
    finally:
        client.close()


def test_v1_gate_plan_does_not_bind_gateway_scope():
    gate = pytest.importorskip(
        "src.job_control.deployment_gate",
        reason="Requires #148 in compatibility worktree",
    )
    binding, _ = fixture_pair()
    fields = dict(
        resource_id=binding.application_uuid,
        role="api",
        current_sha=SHA,
        target_sha=SHA,
        current_image=IMAGE,
        target_image=IMAGE,
        settings_sha256=binding.settings_sha256,
        persistence_sha256=binding.persistence_sha256,
        protected_resources_sha256=binding.protected_resources_sha256,
    )
    plan = gate.Plan(**fields)
    changed = binding.model_dump(mode="json")
    changed["roles"][1]["image"] = "registry.invalid/gateway@sha256:" + "0" * 64
    assert RuntimeBinding.model_validate(changed).digest != binding.digest
    assert gate.Plan(**fields).digest == plan.digest
    with pytest.raises(ValidationError):
        gate.Plan(**fields, runtime_scope_sha256=binding.digest)


def test_no_implicit_network_transport():
    with pytest.raises(Refused):
        CoolifyReadClient(
            "https://coolify.example.invalid",
            ReadScope(application_uuid="fixture", deployment_uuid="fixture"),
            transport=None,
        )


def test_namespace_drift_with_same_container_ids_refused():
    binding, first = fixture_pair()
    second = altered(first, ("roles", 0, "network_namespace"), "restarted_namespace")
    second = altered(second, ("roles", 1, "network_namespace"), "restarted_namespace")
    check_snapshot(binding, second, now=NOW)
    with pytest.raises(Refused):
        check_observation_pair(binding, first, second, now=NOW)
