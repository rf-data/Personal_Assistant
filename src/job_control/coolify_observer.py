"""Offline-testable observer contract. No host transport, commands or Gate driver.

Adapters must independently attest their evidence. A replay success is never a
live production observation, an approval or permission to deploy/resume.
"""

import hashlib
import json
import re
from typing import Annotated, Literal, Protocol

from pydantic import Field, StrictBool, model_validator

from src.job_control.coolify_readiness import (
    GitSha,
    ImageId,
    ImageRef,
    Model,
    Refused,
    Role,
    RuntimeBinding,
    RuntimeRead,
    _unique,
    check_snapshot,
)
from src.job_control.models import Identifier, Sha, canonical

Path = Annotated[str, Field(pattern=r"^/[A-Za-z0-9_./-]+$", max_length=512)]


def fingerprint(value):
    return hashlib.sha256(canonical(value.model_dump(mode="json"))).hexdigest()


class Mount(Model):
    source: Path
    destination: Path
    read_only: StrictBool
    device: int = Field(strict=True, ge=0)
    inode: int = Field(strict=True, gt=0)

    @model_validator(mode="after")
    def portable(self):
        for path in (self.source, self.destination):
            if ".." in path.split("/") or "//" in path or path.endswith("/"):
                raise ValueError("Canonical absolute mount paths required")
        return self


class RoleScope(Model):
    role: Role
    service: Identifier
    revision: GitSha
    image: ImageRef
    image_id: ImageId
    build_receipt_sha256: Sha
    command_sha256: Sha  # reviewed entrypoint + argv; never argv in collector output
    health_contract_sha256: Sha
    readiness_contract_sha256: Sha
    mounts: tuple[Mount, ...] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def ordered_mounts(self):
        if tuple(
            sorted(self.mounts, key=lambda m: m.destination)
        ) != self.mounts or len({m.destination for m in self.mounts}) != len(
            self.mounts
        ):
            raise ValueError("Unique sorted mount destinations required")
        return self


class RuntimeScope(Model):
    """Immutable approved state. No future container/deployment IDs or timestamps."""

    schema_version: Literal[1] = 1
    application_uuid: Identifier
    protected_ui_uuid: Identifier
    server_uuid: Identifier
    environment_uuid: Identifier
    repository: str = Field(pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
    branch: Identifier
    base_directory: Literal["/"] = "/"
    compose_location: Path
    compose_project: Identifier
    compose_sha256: Sha
    settings_sha256: Sha
    persistence_sha256: Sha
    protected_resources_sha256: Sha
    caddy_sha256: Sha
    tls_binding_sha256: Sha
    trigger_policy_sha256: Sha
    allowed_trigger_actors: tuple[Identifier, ...] = Field(min_length=1, max_length=16)
    private_network_id: Sha
    private_network_name: Identifier
    namespace_contract: Literal["api-shares-gateway;worker-isolated"] = (
        "api-shares-gateway;worker-isolated"
    )
    private_network_internal: Literal[True] = True
    published_host_ports: tuple[int, ...] = Field(default=(), max_length=0)
    jobroot: Mount  # actual root identity, separately from its parent bind
    roles: tuple[RoleScope, RoleScope, RoleScope]

    @model_validator(mode="after")
    def coherent(self):
        if (
            tuple(r.role for r in self.roles)
            != ("api", "api-gateway", "capacity-worker")
            or len({r.service for r in self.roles}) != 3
        ):
            raise ValueError("Three sorted unique roles/services required")
        if self.application_uuid == self.protected_ui_uuid:
            raise ValueError("Separate protected UI required")
        api, _, worker = self.roles
        if (api.revision, api.image, api.image_id) != (
            worker.revision,
            worker.image,
            worker.image_id,
        ) or self.jobroot.read_only:
            raise ValueError("Shared backend image and writable jobroot required")
        if (
            tuple(sorted(set(self.allowed_trigger_actors)))
            != self.allowed_trigger_actors
        ):
            raise ValueError("Unique sorted trigger actors required")
        return self

    @property
    def digest(self):
        return fingerprint(self)


class OperationPlan(Model):
    """v2 review envelope, NOT the v1 Gate Plan or an accepted deployment permit."""

    schema_version: Literal[2] = 2
    gate_plan_sha256: Sha
    current: RuntimeScope
    target: RuntimeScope

    @model_validator(mode="after")
    def same_resource(self):
        for name in (
            "application_uuid",
            "protected_ui_uuid",
            "server_uuid",
            "environment_uuid",
            "compose_project",
            "repository",
            "settings_sha256",
            "persistence_sha256",
            "protected_resources_sha256",
        ):
            if getattr(self.current, name) != getattr(self.target, name):
                raise ValueError("One resource and fixed persistence/settings required")
        return self

    @property
    def runtime_scope_sha256(self):
        return fingerprint(self)


def bind_gate_plan(gate_plan, current: RuntimeScope, target: RuntimeScope):
    """Bind an actual #148 Plan without changing its journal or accepting v2 there."""
    from src.job_control.deployment_gate import Plan

    if not isinstance(gate_plan, Plan):
        raise Refused("actual_gate_plan_required")
    for scope, sha, image in (
        (current, gate_plan.current_sha, gate_plan.current_image),
        (target, gate_plan.target_sha, gate_plan.target_image),
    ):
        if (
            gate_plan.role != "api"
            or gate_plan.resource_id != scope.application_uuid
            or (scope.roles[0].revision, scope.roles[0].image) != (sha, image)
            or any(
                getattr(gate_plan, key) != getattr(scope, key)
                for key in (
                    "settings_sha256",
                    "persistence_sha256",
                    "protected_resources_sha256",
                )
            )
        ):
            raise Refused("gate_plan_scope_mismatch")
    return OperationPlan(
        gate_plan_sha256=gate_plan.digest, current=current, target=target
    )


class ObserverBinding(Model):
    schema_version: Literal[1] = 1
    scope: RuntimeScope
    phase: Literal["current", "target"]
    deployment_uuid: Identifier  # late-bound receipt, not guessed before deployment
    host_id: Identifier
    adapter_id: Identifier


class Member(Model):
    container_id: Sha
    application_uuid: Identifier | None
    compose_project: Identifier | None
    writable_sources: tuple[Path, ...] = Field(max_length=16)


class Inventory(Model):
    complete: StrictBool | None
    members: tuple[Member, ...] = Field(max_length=64)


class Container(Model):
    container_id: Sha
    application_uuid: Identifier
    compose_project: Identifier
    service: Identifier
    role: Role
    image_id: ImageId
    command_sha256: Sha | None
    settings_sha256: Sha | None
    mounts: tuple[Mount, ...] = Field(max_length=8)
    jobroot: Mount | None
    running: StrictBool | None
    process_verified: StrictBool | None
    healthy: StrictBool | None
    ready: StrictBool | None
    health_contract_sha256: Sha | None
    readiness_contract_sha256: Sha | None
    network_mode: str = Field(max_length=100)
    network_namespace: Identifier | None
    network_ids: tuple[Sha, ...] = Field(max_length=4)
    host_ports: tuple[int, ...] = Field(max_length=16)
    heartbeat_at: float | None = Field(allow_inf_nan=False)


class Image(Model):
    image_id: ImageId
    repo_digests: tuple[ImageRef, ...] = Field(max_length=8)
    repository: str | None = Field(
        pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", max_length=200
    )
    revision: GitSha | None
    provenance: Literal["verified_build_receipt", "label_only", "unverified"]
    build_receipt_sha256: Sha | None


class Boundary(Model):
    server_uuid: Identifier
    environment_uuid: Identifier
    compose_sha256: Sha | None
    settings_sha256: Sha | None
    persistence_sha256: Sha | None
    protected_resources_sha256: Sha | None
    caddy_sha256: Sha | None
    tls_binding_sha256: Sha | None
    trigger_policy_sha256: Sha | None
    trigger_inventory_complete: StrictBool | None
    trigger_actors: tuple[Identifier, ...] = Field(max_length=16)
    private_network_id: Sha | None
    private_network_internal: StrictBool | None
    tls_verified: StrictBool | None
    external_intake_fenced: StrictBool | None
    external_jobs_idle: StrictBool | None
    writer_inventory_complete: StrictBool | None
    jobroot_writer_ids: tuple[Sha, ...] = Field(max_length=16)


class Provenance(Model):
    schema_version: Literal[1] = 1
    collector_version: Literal["c26-host-metadata/1"] = "c26-host-metadata/1"
    mode: Literal["offline_fixture"] = "offline_fixture"
    host_id: Identifier
    adapter_id: Identifier
    observed_at: float = Field(allow_inf_nan=False)


class HostEvidence(Model):
    provenance: Provenance
    inventory: Inventory
    boundary: Boundary
    containers: tuple[Container, ...] = Field(max_length=3)
    images: tuple[Image, ...] = Field(max_length=3)


class MetadataAdapter(Protocol):
    """A future authenticated host transport needs separate operator approval.

    Queries return pre-projected JSON, never raw Docker inspect/env/logs. Query
    meanings: complete host inventory; one container; one image; independent
    boundary attestation. No URL, command or caller-selected query is accepted.
    """

    def query(
        self,
        query: Literal["inventory", "container", "image", "boundary"],
        identity: str | None,
    ) -> bytes: ...


class HostCollector:
    """Fixed bounded metadata queries. Only injected offline adapters supported."""

    def __init__(self, *, adapter: MetadataAdapter, host_id, adapter_id, clock):
        self.adapter = adapter
        self.host_id, self.adapter_id, self.clock = host_id, adapter_id, clock

    def _query(self, query, identity, model):
        allowed = {
            "inventory": (Inventory, identity is None),
            "container": (
                Container,
                isinstance(identity, str)
                and re.fullmatch(r"[a-f0-9]{64}", identity) is not None,
            ),
            "image": (
                Image,
                isinstance(identity, str)
                and re.fullmatch(r"sha256:[a-f0-9]{64}", identity) is not None,
            ),
            "boundary": (
                Boundary,
                isinstance(identity, str)
                and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", identity)
                is not None,
            ),
        }
        if query not in allowed or allowed[query] != (model, True):
            raise Refused("collector_query_not_allowed")
        try:
            raw = self.adapter.query(query, identity)
            if not isinstance(raw, bytes) or len(raw) > 65536:
                raise Refused("collector_output_limit")
            data = json.loads(raw, object_pairs_hook=_unique)
            if not isinstance(data, dict):
                raise Refused("collector_object_required")
            # Top-level allowlist. Nested records are strict; nothing raw is logged.
            return model.model_validate(
                {k: v for k, v in data.items() if k in model.model_fields}
            )
        except Exception:
            raise Refused("collector_metadata_unverified") from None

    def collect(self, binding: ObserverBinding):
        if self.host_id != binding.host_id or self.adapter_id != binding.adapter_id:
            raise Refused("collector_provenance_mismatch")
        started_at = self.clock()
        inventory = self._query("inventory", None, Inventory)
        ids = [m.container_id for m in inventory.members]
        if inventory.complete is not True or len(set(ids)) != len(ids):
            raise Refused("complete_unique_host_inventory_required")
        members = [
            m
            for m in inventory.members
            if m.application_uuid == binding.scope.application_uuid
            or m.compose_project == binding.scope.compose_project
        ]
        if len(members) != 3:
            raise Refused("exact_three_resource_members_required")
        containers = tuple(
            self._query("container", m.container_id, Container) for m in members
        )
        if any(
            c.container_id != m.container_id
            for c, m in zip(containers, members, strict=True)
        ):
            raise Refused("collector_membership_contradiction")
        images = tuple(
            self._query("image", image_id, Image)
            for image_id in sorted({c.image_id for c in containers})
        )
        if any(
            image.image_id != expected
            for image, expected in zip(
                images, sorted({c.image_id for c in containers}), strict=True
            )
        ):
            raise Refused("collector_image_contradiction")
        return HostEvidence(
            provenance=Provenance(
                host_id=self.host_id, adapter_id=self.adapter_id, observed_at=started_at
            ),
            inventory=inventory,
            boundary=self._query("boundary", binding.scope.application_uuid, Boundary),
            containers=containers,
            images=images,
        )


class ObserverReport(Model):
    schema_version: Literal[1] = 1
    status: Literal["verified_offline", "NO-GO"]
    runtime_scope_sha256: Sha
    binding_sha256: Sha | None = None
    evidence_sha256: Sha | None = None
    instance_sha256: Sha | None = None
    observed_at: float | None = None
    reasons: tuple[str, ...] = ()
    unverified: tuple[str, ...] = ()
    deployment_permitted: Literal[False] = False
    production_release: Literal["blocked"] = "blocked"


def _verify_host(scope, evidence):
    boundary = evidence.boundary
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
    ):
        if getattr(boundary, name) != getattr(scope, name):
            raise Refused("boundary_scope_unverified")
    if (
        any(
            getattr(boundary, name) is not True
            for name in (
                "trigger_inventory_complete",
                "private_network_internal",
                "tls_verified",
                "external_intake_fenced",
                "external_jobs_idle",
                "writer_inventory_complete",
            )
        )
        or tuple(sorted(boundary.trigger_actors)) != scope.allowed_trigger_actors
    ):
        raise Refused("triggers_network_or_writers_unverified")
    roles = {c.role: c for c in evidence.containers}
    if (
        set(roles) != {r.role for r in scope.roles}
        or len({c.container_id for c in evidence.containers}) != 3
    ):
        raise Refused("unique_roles_required")
    ids = {c.container_id for c in evidence.containers}
    members = [
        m
        for m in evidence.inventory.members
        if m.application_uuid == scope.application_uuid
        or m.compose_project == scope.compose_project
    ]
    if {m.container_id for m in members} != ids:
        raise Refused("collector_membership_contradiction")
    # Complete host inventory: even another Application may mount this writable root.
    runtime_sources = {
        m.source for r in scope.roles for m in r.mounts if not m.read_only
    }
    if any(
        m.container_id not in ids
        and any(
            source == root
            or source.startswith(root + "/")
            or root.startswith(source + "/")
            for source in m.writable_sources
            for root in runtime_sources | {scope.jobroot.source}
        )
        for m in evidence.inventory.members
    ):
        raise Refused("additional_persistence_writer")
    writers = boundary.jobroot_writer_ids
    if len(writers) != 2 or set(writers) != {
        roles[r].container_id for r in ("api", "capacity-worker")
    }:
        raise Refused("jobroot_writers_unverified")
    image_map = {image.image_id: image for image in evidence.images}
    if len(image_map) != len(evidence.images) or set(image_map) != {
        c.image_id for c in evidence.containers
    }:
        raise Refused("collector_image_contradiction")
    role_reads = []
    for expected in scope.roles:
        actual = roles[expected.role]
        if (
            actual.application_uuid != scope.application_uuid
            or actual.compose_project != scope.compose_project
            or actual.service != expected.service
            or actual.image_id != expected.image_id
            or actual.command_sha256 != expected.command_sha256
            or actual.mounts != expected.mounts
            or actual.health_contract_sha256 != expected.health_contract_sha256
            or actual.readiness_contract_sha256 != expected.readiness_contract_sha256
            or actual.running is not True
            or actual.process_verified is not True
            or actual.host_ports
            or actual.network_namespace is None
        ):
            raise Refused("role_command_mount_health_or_ports_unverified")
        member = next(m for m in members if m.container_id == actual.container_id)
        if set(member.writable_sources) != {
            m.source for m in actual.mounts if not m.read_only
        }:
            raise Refused("collector_membership_contradiction")
        if actual.role != "api-gateway" and actual.jobroot != scope.jobroot:
            raise Refused("jobroot_identity_unverified")
        if (
            actual.role != "api-gateway"
            and actual.settings_sha256 != scope.settings_sha256
        ):
            raise Refused("role_settings_unverified")
        image = image_map.get(actual.image_id)
        if (
            image is None
            or expected.image not in image.repo_digests
            or image.repository != scope.repository
            or image.revision != expected.revision
            or image.provenance != "verified_build_receipt"
            or image.build_receipt_sha256 != expected.build_receipt_sha256
        ):
            raise Refused("image_build_provenance_unverified")
        networks = (scope.private_network_id,) if actual.role == "api-gateway" else ()
        if actual.network_ids != networks:
            raise Refused("private_network_membership_unverified")
        role_reads.append(
            dict(
                role=actual.role,
                revision=image.revision,
                image=expected.image,
                image_id=actual.image_id,
                mounts_sha256=hashlib.sha256(
                    canonical([m.model_dump(mode="json") for m in actual.mounts])
                ).hexdigest(),
                container_id=actual.container_id,
                network_mode=actual.network_mode,
                network_namespace=actual.network_namespace,
                healthy=actual.healthy is True,
                ready=actual.ready is True,
                heartbeat_at=actual.heartbeat_at,
            )
        )
    return role_reads


def observe_runtime(
    binding: ObserverBinding, plan: OperationPlan, *, collector, client, now
):
    """One bounded offline observation. Never converted into #148 Observation."""
    if not isinstance(binding, ObserverBinding) or not isinstance(plan, OperationPlan):
        raise Refused("typed_binding_and_operation_required")
    try:
        scope = binding.scope
        if getattr(plan, binding.phase) != scope:
            raise Refused("operation_binding_mismatch")
        if (client.scope.application_uuid, client.scope.deployment_uuid) != (
            scope.application_uuid,
            binding.deployment_uuid,
        ):
            raise Refused("client_scope_mismatch")
        app, deployment = client.application(), client.deployment()
        evidence = collector.collect(binding)
        provenance = evidence.provenance
        if (provenance.host_id, provenance.adapter_id) != (
            binding.host_id,
            binding.adapter_id,
        ):
            raise Refused("collector_provenance_mismatch")
        role_reads = _verify_host(scope, evidence)
        roles = {r.role: r for r in scope.roles}
        legacy = RuntimeBinding(
            **{
                k: getattr(scope, k)
                for k in (
                    "application_uuid",
                    "protected_ui_uuid",
                    "server_uuid",
                    "environment_uuid",
                    "repository",
                    "branch",
                    "base_directory",
                    "compose_location",
                    "compose_project",
                    "settings_sha256",
                    "persistence_sha256",
                    "protected_resources_sha256",
                    "trigger_policy_sha256",
                    "private_network_id",
                    "private_network_name",
                    "tls_binding_sha256",
                )
            },
            git_commit_sha=roles["api"].revision,
            deployment_uuid=binding.deployment_uuid,
            roles=[
                {
                    k: r[k]
                    for k in ("role", "revision", "image", "image_id", "mounts_sha256")
                }
                for r in role_reads
            ],
        )
        reading = RuntimeRead(
            **{
                k: getattr(legacy, k)
                for k in (
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
            },
            inventory_complete=evidence.inventory.complete,
            resource_container_ids=[c.container_id for c in evidence.containers],
            application=app,
            deployment=deployment,
            binding_sha256=legacy.digest,
            tls_verified=True,
            additional_triggers_controlled=True,
            external_intake_fenced=True,
            external_jobs_idle=True,
            observed_at=provenance.observed_at,
            roles=role_reads,
        )
        check_snapshot(legacy, reading, now=now)
        instances = sorted(
            (r.role, r.container_id, r.network_namespace) for r in reading.roles
        )
        return ObserverReport(
            status="verified_offline",
            runtime_scope_sha256=plan.runtime_scope_sha256,
            binding_sha256=fingerprint(binding),
            evidence_sha256=fingerprint(evidence),
            instance_sha256=hashlib.sha256(canonical(instances)).hexdigest(),
            observed_at=provenance.observed_at,
        )
    except Exception as error:
        reason = "runtime_evidence_unverified"
        if isinstance(error, Refused) and str(error) in {
            "operation_binding_mismatch",
            "client_scope_mismatch",
            "collector_provenance_mismatch",
            "collector_metadata_unverified",
            "complete_unique_host_inventory_required",
            "exact_three_resource_members_required",
            "boundary_scope_unverified",
            "triggers_network_or_writers_unverified",
            "unique_roles_required",
            "collector_membership_contradiction",
            "additional_persistence_writer",
            "jobroot_writers_unverified",
            "collector_image_contradiction",
            "role_command_mount_health_or_ports_unverified",
            "jobroot_identity_unverified",
            "role_settings_unverified",
            "image_build_provenance_unverified",
            "private_network_membership_unverified",
            "fresh_complete_observation_required",
            "resource_build_revision_or_trigger_mismatch",
            "role_health_unconfirmed",
            "namespace_or_worker_heartbeat_unconfirmed",
        }:
            reason = str(error)
        return ObserverReport(
            status="NO-GO",
            runtime_scope_sha256=plan.runtime_scope_sha256,
            reasons=(reason,),
            unverified=(reason,),
        )


def check_runtime_pair(first: ObserverReport, second: ObserverReport, *, now):
    if any(
        r is None
        or r.status != "verified_offline"
        or r.observed_at is None
        or not 0 <= now - r.observed_at <= 30
        for r in (first, second)
    ):
        raise Refused("complete_fresh_observation_pair_required")
    if (
        first.runtime_scope_sha256 != second.runtime_scope_sha256
        or first.binding_sha256 != second.binding_sha256
        or first.instance_sha256 != second.instance_sha256
        or second.observed_at < first.observed_at
    ):
        raise Refused("runtime_scope_or_instance_drift")
    return second
