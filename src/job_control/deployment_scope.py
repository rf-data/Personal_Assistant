"""Versioned offline v2 bindings. No transport, credentials or new state machine."""

import hashlib
import time
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Literal

from pydantic import Field, model_validator

from src.job_control.coolify_observer import (
    HostEvidence,
    ObserverBinding,
    OperationPlan,
    bind_gate_plan,
    observe_runtime,
)
from src.job_control.coolify_readiness import ApplicationRead, DeploymentRead
from src.job_control.deployment_gate import Approval, Blocked, Plan, _lock
from src.job_control.models import Contract, Identifier, Sha, canonical


def snapshot(value, expected, maximum=262144):
    try:
        if type(value) is not expected:
            raise ValueError("Exact version required")
        raw = canonical(value.model_dump(mode="json", warnings=False))
        if len(raw) > maximum:
            raise ValueError("Bounded document required")
        return expected.model_validate_json(raw)
    except (TypeError, ValueError, AttributeError):
        raise Blocked("v2_document_invalid") from None


def strict_versions(value):
    if isinstance(value, dict):
        if "schema_version" in value and type(value["schema_version"]) is not int:
            raise ValueError("Integer schema versions required")
        for item in value.values():
            strict_versions(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            strict_versions(item)
    return value


class VersionedV2:
    @model_validator(mode="before")
    @classmethod
    def versions(cls, value):
        return strict_versions(value)


class PlanV2(VersionedV2, Plan):
    schema_version: Literal[2] = 2
    protocol: Literal["c26-gate-v2"] = "c26-gate-v2"
    mode: Literal["offline_fixture"] = "offline_fixture"
    operation: OperationPlan

    def legacy(self):
        return Plan(**{key: getattr(self, key) for key in Plan.model_fields})

    @model_validator(mode="after")
    def bound(self):
        expected = bind_gate_plan(
            self.legacy(), self.operation.current, self.operation.target
        )
        if (
            expected != self.operation
            or self.operation.current.jobroot != self.operation.target.jobroot
        ):
            raise ValueError(
                "Complete operation and fixed jobroot must match gate plan"
            )
        return self


class ApprovalV2(VersionedV2, Approval):
    schema_version: Literal[2] = 2
    protocol: Literal["c26-gate-v2"] = "c26-gate-v2"
    mode: Literal["offline_fixture"] = "offline_fixture"
    runtime_scope_sha256: Sha

    def check(self, plan, action):
        if (
            type(plan) is not PlanV2
            or self.runtime_scope_sha256 != plan.operation.runtime_scope_sha256
        ):
            raise Blocked("v2_approval_scope_mismatch")
        super().check(plan, action)


class ObservationV2(VersionedV2, Contract):
    schema_version: Literal[2] = 2
    protocol: Literal["c26-gate-v2"] = "c26-gate-v2"
    mode: Literal["offline_fixture"] = "offline_fixture"
    binding: ObserverBinding
    evidence: HostEvidence
    application: ApplicationRead
    deployment: DeploymentRead

    @property
    def observed_at(self):
        return self.evidence.provenance.observed_at

    @property
    def container_id(self):
        instances = sorted(
            (c.role, c.container_id, c.network_namespace)
            for c in self.evidence.containers
        )
        return hashlib.sha256(canonical(instances)).hexdigest()

    def check(self, plan, *, target, require_health=True):
        if self.binding.phase != ("target" if target else "current"):
            raise Blocked("v2_observation_phase_mismatch")
        if any(
            type(c.healthy) is not bool or type(c.ready) is not bool
            for c in self.evidence.containers
        ):
            raise Blocked("v2_health_state_unknown")
        # Reuse the existing observer with already collected, typed fixture data.
        # These objects expose no HTTP transport or host access.
        client = SimpleNamespace(
            scope=SimpleNamespace(
                application_uuid=self.binding.scope.application_uuid,
                deployment_uuid=self.binding.deployment_uuid,
            ),
            application=lambda: self.application,
            deployment=lambda: self.deployment,
        )
        report = observe_runtime(
            self.binding,
            plan.operation,
            collector=SimpleNamespace(collect=lambda binding: self.evidence),
            client=client,
            now=time.time(),
            require_health=require_health,
        )
        if (
            report.status != "verified_offline"
            or report.runtime_scope_sha256 != plan.operation.runtime_scope_sha256
        ):
            raise Blocked("v2_runtime_evidence_unverified")
        return self


class JournalEventV2(VersionedV2, Contract):
    schema_version: Literal[2] = 2
    protocol: Literal["c26-gate-v2"] = "c26-gate-v2"
    mode: Literal["offline_fixture"] = "offline_fixture"
    sequence: int = Field(strict=True, ge=1)
    previous: Sha
    at: float = Field(strict=True, allow_inf_nan=False, ge=0)
    phase: Literal[
        "held", "open", "draining", "deploying", "verifying", "verified", "recovery"
    ]
    operation: Identifier | None
    plan: PlanV2 | None
    approval: ApprovalV2 | None
    runtime_scope_sha256: Sha | None
    reason: Identifier
    sha256: Sha

    @model_validator(mode="after")
    def bound(self):
        scope = self.plan.operation.runtime_scope_sha256 if self.plan else None
        if self.runtime_scope_sha256 != scope:
            raise ValueError("Journal scope mismatch")
        if self.approval and (
            self.plan is None
            or self.approval.plan_sha256 != self.plan.digest
            or self.approval.runtime_scope_sha256 != scope
            or self.operation != self.approval.approval_id
        ):
            raise ValueError("Journal approval mismatch")
        if self.phase not in {"held", "recovery"} and self.plan is None:
            raise ValueError("Journal plan required")
        return self


def replacement(plan, before, after):
    if (before.binding.host_id, before.binding.adapter_id) != (
        after.binding.host_id,
        after.binding.adapter_id,
    ):
        raise Blocked("v2_collector_binding_changed")
    if before.binding.deployment_uuid == after.binding.deployment_uuid:
        raise Blocked("v2_new_deployment_receipt_required")
    old = {c.role: c for c in before.evidence.containers}
    new = {c.role: c for c in after.evidence.containers}
    for current, target in zip(
        plan.operation.current.roles, plan.operation.target.roles, strict=True
    ):
        if (
            current != target
            and old[current.role].container_id == new[target.role].container_id
        ):
            raise Blocked("v2_changed_role_not_replaced")


@dataclass
class PermitV2:
    gate: object
    plan: PlanV2
    operation: str
    approval: ApprovalV2
    driver: object
    before: ObservationV2
    active: bool = True
    mode: Literal["offline_fixture"] = "offline_fixture"

    def check(self):
        seal = self.gate._active_permit
        if (
            self.mode != "offline_fixture"
            or not self.active
            or seal is None
            or seal[0] is not self
        ):
            raise Blocked("v2_permit_session_expired")
        plan = snapshot(self.plan, PlanV2, 65536)
        approval = snapshot(self.approval, ApprovalV2)
        if (
            plan.digest,
            approval.model_dump_json(),
            self.operation,
            id(self.driver),
            self.before.container_id,
            self.before.binding.model_dump_json(),
        ) != seal[1:]:
            raise Blocked("v2_permit_binding_changed")
        observed = self.gate._observe(
            self.driver,
            plan,
            target=False,
            require_health=approval.action != "rollback",
        )
        if (
            observed.container_id != self.before.container_id
            or observed.binding != self.before.binding
        ):
            raise Blocked("v2_prechange_instance_drift")
        with _lock(self.gate.root, ".deployment-admission.lock", timeout=2):
            self._check_state(plan, approval)

    def _check_state(self, plan, approval):
        from src.job_control.deployment_gate import _read

        state = _read(self.gate.root, version=2)[-1]
        if (
            state["phase"] != "deploying"
            or state["operation"] != self.operation
            or state["plan"] != plan.model_dump(mode="json")
            or state["approval"] != approval.model_dump(mode="json")
        ):
            raise Blocked("v2_permit_journal_mismatch")
        self.gate._idle()
        self.gate._approval(plan, approval, approval.action)

    def claim(self):
        """Exactly one synthetic side effect per active owner session."""
        self.check()
        with _lock(self.gate.root, ".deployment-admission.lock", timeout=2):
            self._check_state(self.plan, self.approval)
            if self.gate._permit_claimed:
                raise Blocked("v2_permit_already_claimed")
            self.gate._permit_claimed = True
