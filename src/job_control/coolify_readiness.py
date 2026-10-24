"""Coolify 4.4.7 read projection and offline consistency checks, never a Driver.

No CLI, default network transport, credential loading, queue access or mutating
operation. Replayed evidence is not a live Gate Observation or deployment permit.
"""

import hashlib
import json
import math
import re
from typing import Annotated, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from src.job_control.models import Identifier, Sha, canonical

GitSha = Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
ImageId = Annotated[str, Field(pattern=r"^sha256:[a-f0-9]{64}$")]
ImageRef = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*(/[A-Za-z0-9][A-Za-z0-9._:-]*)*@sha256:[a-f0-9]{64}$"
    ),
]
Role = Literal["api", "api-gateway", "capacity-worker"]
ROLES = {"api", "api-gateway", "capacity-worker"}


class Refused(ValueError):
    """Fixed diagnostic only; response bodies and credentials are never echoed."""


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReadScope(Model):
    application_uuid: Identifier
    deployment_uuid: Identifier


class ApplicationRead(Model):
    uuid: Identifier
    build_pack: Literal["dockerfile", "dockercompose"]
    git_repository: str | None
    git_branch: str | None
    git_commit_sha: str | None
    base_directory: str | None
    docker_compose_location: str | None
    auto_deploy_enabled: StrictBool | None
    preview_deployments_enabled: StrictBool | None


class DeploymentRead(Model):
    deployment_uuid: Identifier
    commit: str = Field(max_length=200)
    status: Literal["queued", "in_progress", "finished", "failed", "cancelled-by-user"]
    pull_request_id: int = Field(strict=True, ge=0)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refused("duplicate_response_key")
        result[key] = value
    return result


class CoolifyReadClient:
    """Only two fixed GET paths, exact pre-bound UUIDs; injected transport required.

    Auth may be supplied by a separately approved caller. Never use read:sensitive
    or root tokens. This library reads no local credentials and logs no responses.
    """

    def __init__(self, origin, scope: ReadScope, *, transport, auth=None):
        url = httpx.URL(origin)
        if (
            url.scheme != "https"
            or not url.host
            or url.userinfo
            or url.query
            or url.fragment
            or url.path != "/"
        ):
            raise Refused("explicit_https_origin_required")
        if not isinstance(transport, httpx.BaseTransport):
            raise Refused("explicit_transport_required")
        self.scope = ReadScope.model_validate(scope)
        self.client = httpx.Client(
            base_url=str(url),
            transport=transport,
            auth=auth,
            timeout=3,
            follow_redirects=False,
            trust_env=False,
            headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        )

    def close(self):
        self.client.close()

    def _read(self, path):
        allowed = {
            "/api/v1/applications/" + self.scope.application_uuid,
            "/api/v1/deployments/applications/"
            + self.scope.application_uuid
            + "?skip=0&take=16",
        }
        if path not in allowed:
            raise Refused("read_endpoint_not_allowed")
        try:
            with self.client.stream("GET", path) as response:
                if (
                    response.status_code != 200
                    or response.headers.get("content-encoding", "identity")
                    != "identity"
                ):
                    raise Refused("coolify_read_refused")
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=8192):
                    body.extend(chunk)
                    if len(body) > 131072:
                        raise Refused("bounded_response_required")
                data = json.loads(body, object_pairs_hook=_unique)
                if not isinstance(data, dict):
                    raise Refused("response_object_required")
                return data
        except (httpx.HTTPError, ValueError, TypeError):
            raise Refused("coolify_read_refused") from None

    def application(self):
        raw = self._read("/api/v1/applications/" + self.scope.application_uuid)
        try:
            settings = raw.get("settings") or {}
            # Explicit allowlist: never expose envs, logs, commands, webhook
            # secrets, raw compose or arbitrary configuration snapshots.
            keys = (
                "uuid",
                "build_pack",
                "git_repository",
                "git_branch",
                "git_commit_sha",
                "base_directory",
                "docker_compose_location",
            )
            result = ApplicationRead(
                **{key: raw.get(key) for key in keys},
                auto_deploy_enabled=settings.get("is_auto_deploy_enabled"),
                preview_deployments_enabled=settings.get(
                    "is_preview_deployments_enabled"
                ),
            )
            if (
                result.git_repository is not None
                and re.fullmatch(
                    r"(?:https://github.com/|git@github.com:)?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
                    result.git_repository,
                )
                is None
            ):
                raise Refused("safe_repository_metadata_required")
            if result.uuid != self.scope.application_uuid:
                raise Refused("application_scope_mismatch")
            return result
        except (ValueError, TypeError, AttributeError):
            raise Refused("application_projection_refused") from None

    def deployment(self):
        # Application-scoped history establishes membership without guessing a
        # hidden numeric application ID. No generic /deploy or arbitrary URL.
        path = "/api/v1/deployments/applications/" + self.scope.application_uuid
        raw = self._read(path + "?skip=0&take=16")
        try:
            rows = raw["deployments"]
            if not isinstance(rows, list) or len(rows) > 16:
                raise Refused("bounded_history_required")
            matches = [
                row
                for row in rows
                if row.get("deployment_uuid") == self.scope.deployment_uuid
            ]
            if len(matches) != 1:
                raise Refused("exact_deployment_membership_required")
            keys = ("deployment_uuid", "commit", "status", "pull_request_id")
            return DeploymentRead(**{key: matches[0].get(key) for key in keys})
        except (ValueError, TypeError, KeyError, AttributeError):
            raise Refused("deployment_projection_refused") from None


class RoleBinding(Model):
    role: Role
    revision: GitSha
    image: ImageRef
    image_id: ImageId
    mounts_sha256: Sha


class RuntimeBinding(Model):
    """Reviewed intended runtime, not a template that approves today's inventory."""

    schema_version: Literal[1] = 1
    application_uuid: Identifier
    protected_ui_uuid: Identifier
    deployment_uuid: Identifier
    server_uuid: Identifier
    environment_uuid: Identifier
    repository: str = Field(min_length=1, max_length=512)
    branch: str = Field(min_length=1, max_length=200)
    base_directory: str = Field(min_length=1, max_length=512)
    compose_location: str = Field(min_length=1, max_length=512)
    compose_project: Identifier
    git_commit_sha: GitSha
    settings_sha256: Sha
    persistence_sha256: Sha
    protected_resources_sha256: Sha
    trigger_policy_sha256: Sha
    private_network_id: Sha
    private_network_name: Identifier
    tls_binding_sha256: Sha
    roles: tuple[RoleBinding, RoleBinding, RoleBinding]

    @model_validator(mode="after")
    def coherent_roles(self):
        roles = {role.role: role for role in self.roles}
        if set(roles) != ROLES or self.application_uuid == self.protected_ui_uuid:
            raise ValueError("Exact separate runtime/UI scope required")
        api, worker = roles["api"], roles["capacity-worker"]
        if (
            api.revision != worker.revision
            or api.revision != self.git_commit_sha
            or api.image != worker.image
            or api.image_id != worker.image_id
            or api.mounts_sha256 != worker.mounts_sha256
        ):
            raise ValueError("Shared backend revision/image/mount contract required")
        return self

    @property
    def digest(self):
        return hashlib.sha256(canonical(self.model_dump(mode="json"))).hexdigest()


class RoleRead(RoleBinding):
    container_id: Sha
    network_mode: str = Field(min_length=1, max_length=200)
    network_namespace: Identifier
    healthy: StrictBool
    ready: StrictBool
    heartbeat_at: float | None = Field(default=None, allow_inf_nan=False)


class RuntimeRead(Model):
    inventory_complete: StrictBool
    resource_container_ids: tuple[Sha, ...] = Field(min_length=1, max_length=64)
    application: ApplicationRead
    deployment: DeploymentRead
    binding_sha256: Sha
    server_uuid: Identifier
    environment_uuid: Identifier
    compose_project: Identifier
    settings_sha256: Sha
    persistence_sha256: Sha
    protected_resources_sha256: Sha
    trigger_policy_sha256: Sha
    private_network_id: Sha
    tls_binding_sha256: Sha
    tls_verified: StrictBool
    additional_triggers_controlled: StrictBool
    external_intake_fenced: StrictBool
    external_jobs_idle: StrictBool
    observed_at: float = Field(allow_inf_nan=False)
    roles: tuple[RoleRead, RoleRead, RoleRead]


class ConsistencyReport(Model):
    binding_sha256: Sha
    replay_consistent: Literal[True] = True
    deployment_permitted: Literal[False] = False
    production_release: Literal["blocked"] = "blocked"


def check_snapshot(
    binding: RuntimeBinding, reading: RuntimeRead, *, now: float, require_health=True
):
    """Pure replay consistency; claimed health must still come from a live collector."""
    if not isinstance(binding, RuntimeBinding) or not isinstance(reading, RuntimeRead):
        raise Refused("typed_evidence_required")
    if not math.isfinite(now) or not 0 <= now - reading.observed_at <= 30:
        raise Refused("fresh_complete_observation_required")
    app, deployment = reading.application, reading.deployment
    if (
        app.uuid != binding.application_uuid
        or app.build_pack != "dockercompose"
        or app.git_repository != binding.repository
        or app.git_branch != binding.branch
        or app.git_commit_sha != binding.git_commit_sha
        or app.base_directory != binding.base_directory
        or app.docker_compose_location != binding.compose_location
        or app.auto_deploy_enabled is not False
        or app.preview_deployments_enabled is not False
        or deployment.deployment_uuid != binding.deployment_uuid
        or deployment.commit != binding.git_commit_sha
        or deployment.status != "finished"
        or deployment.pull_request_id != 0
        or reading.binding_sha256 != binding.digest
    ):
        raise Refused("resource_build_revision_or_trigger_mismatch")
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
    ):
        if getattr(reading, name) != getattr(binding, name):
            raise Refused("runtime_scope_mismatch")
    if not all(
        (
            reading.tls_verified,
            reading.additional_triggers_controlled,
            reading.external_intake_fenced,
            reading.external_jobs_idle,
        )
    ):
        raise Refused("runtime_boundary_unconfirmed")
    roles = {role.role: role for role in reading.roles}
    if (
        set(roles) != ROLES
        or len({role.container_id for role in reading.roles}) != 3
        or not reading.inventory_complete
        or len(reading.resource_container_ids) != 3
        or set(reading.resource_container_ids)
        != {role.container_id for role in reading.roles}
    ):
        raise Refused("exact_three_role_instances_required")
    for expected in binding.roles:
        actual = roles[expected.role]
        for name in RoleBinding.model_fields:
            if getattr(actual, name) != getattr(expected, name):
                raise Refused("role_image_revision_or_mount_mismatch")
        if require_health and (not actual.healthy or not actual.ready):
            raise Refused("role_health_unconfirmed")
    api, gateway, worker = roles["api"], roles["api-gateway"], roles["capacity-worker"]
    if (
        gateway.network_mode != binding.private_network_name
        or api.network_mode != "container:" + gateway.container_id
        or api.network_namespace != gateway.network_namespace
        or worker.network_mode != "none"
        or worker.network_namespace == api.network_namespace
        or worker.heartbeat_at is None
        or not 0 <= now - worker.heartbeat_at < 10
    ):
        raise Refused("namespace_or_worker_heartbeat_unconfirmed")
    return ConsistencyReport(binding_sha256=binding.digest)


def check_observation_pair(binding, first, second, *, now):
    """A missing/interrupted or drifting pair cannot preserve a former success."""
    if first is None or second is None:
        raise Refused("complete_new_observation_pair_required")
    check_snapshot(binding, first, now=now)
    result = check_snapshot(binding, second, now=now)
    first_instances = {
        r.role: (r.container_id, r.network_mode, r.network_namespace)
        for r in first.roles
    }
    second_instances = {
        r.role: (r.container_id, r.network_mode, r.network_namespace)
        for r in second.roles
    }
    if (
        first_instances != second_instances
        or first.deployment != second.deployment
        or second.observed_at < first.observed_at
    ):
        raise Refused("observation_interrupted_or_instance_drift")
    return result
