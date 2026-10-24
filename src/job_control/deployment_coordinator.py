"""Independent C26-F OFFLINE coordinator over C26-D; no signer or live driver.

Use in a separate trusted process outside replaced roles. All supplied runtime
proofs must be synthetic; productive trust/transport/authorization is disabled.
"""

import os
import secrets
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import Field

from src.job_control.coolify_observer import fingerprint
from src.job_control.coordinator_state import (
    ENROLLMENT,
    SESSION_LOCK,
    Enrollment,
    LocalTestWitness,
    Refused,
    enrollment,
    root_identity,
)
from src.job_control.deployment_gate import (
    LOCK,
    Busy,
    Gate,
    _append,
    _fd,
    _lock,
    _read,
)
from src.job_control.deployment_scope import (
    ApprovalV2,
    ObservationV2,
    PlanV2,
    VersionedV2,
    snapshot,
)
from src.job_control.models import Contract, Identifier, Sha, canonical
from src.job_control.runtime_collector import Capture

Action = Literal["deploy", "rollback", "recover", "resume"]


class Challenge(VersionedV2, Contract):
    schema_version: Literal[1] = 1
    protocol: Literal["c26-coordinator/1"] = "c26-coordinator/1"
    mode: Literal["offline_fixture"] = "offline_fixture"
    session_id: Sha
    epoch: int = Field(strict=True, gt=0)
    root_id: Sha
    action: Action
    resource_id: Identifier
    server_id: Identifier
    environment_id: Identifier
    plan_sha256: Sha
    runtime_scope_sha256: Sha
    sequence: int = Field(strict=True, ge=1)
    journal_sha256: Sha
    instance_sha256: Sha
    evidence_sha256: Sha
    created_at: float = Field(strict=True, allow_inf_nan=False)
    expires_at: float = Field(strict=True, allow_inf_nan=False)


class OperatorGrant(VersionedV2, Contract):
    schema_version: Literal[1] = 1
    mode: Literal["offline_fixture"] = "offline_fixture"
    grant_id: Identifier
    issuer: Identifier
    subject: Identifier
    role: Literal["observer", "operator"]
    challenge: Challenge
    issued_at: float = Field(strict=True, allow_inf_nan=False)
    expires_at: float = Field(strict=True, allow_inf_nan=False)


class SignedGrant(VersionedV2, Contract):
    schema_version: Literal[1] = 1
    mode: Literal["fixture_authority"] = "fixture_authority"
    grant: OperatorGrant
    signature: Sha


class GrantVerifier(Protocol):
    """Trusted injected fixture verifier. Coordinator never receives signing keys."""

    def verify(self, envelope: SignedGrant) -> OperatorGrant: ...


class DriverReceipt(VersionedV2, Contract):
    schema_version: Literal[1] = 1
    mode: Literal["inert"] = "inert"
    session_id: Sha
    epoch: int = Field(strict=True, gt=0)
    plan_sha256: Sha
    grant_id: Identifier
    status: Literal["completed", "failed", "uncertain"]


class InertDriver:
    """Only in-memory fixture state changes. No transport, commands or real driver."""

    def __init__(self, scope, *, generation=0, hook=lambda stage: None):
        self.scope, self.generation, self.hook = scope, generation, hook
        self.calls = 0

    def change(self, plan, permit):
        if type(permit) is not _Permit:
            raise Refused("coordinator_bound_permit_required")
        self.hook("before_claim")
        permit.claim()
        self.hook("after_claim")
        permit.check()
        self.scope = plan.operation.target
        self.generation += 1
        self.calls += 1
        self.hook("after_change")
        return DriverReceipt(
            session_id=permit.session.challenge.session_id,
            epoch=permit.session.challenge.epoch,
            plan_sha256=plan.digest,
            grant_id=permit.session.grant.grant_id,
            status="completed",
        )


class OfflineCoordinator:
    def __init__(
        self,
        settings,
        *,
        witness,
        verifier: GrantVerifier,
        evidence,
        driver,
        clock=time.time,
    ):
        if (
            not settings.coordinator_test_required
            or settings.deployment_gate_protocol != "c26-gate-v2"
            or type(witness) is not LocalTestWitness
            or type(driver) is not InertDriver
        ):
            raise Refused("coordinator_explicit_offline_profile_required")
        self.settings, self.root = settings, settings.root
        self.witness, self.verifier = witness, verifier
        self.evidence, self.driver, self.clock = evidence, driver, clock

    @staticmethod
    def enroll(settings, witness):
        """Explicit test bootstrap on existing v2 queue; never opens admissions."""
        if (
            not settings.coordinator_test_required
            or type(witness) is not LocalTestWitness
            or witness.path.is_relative_to(settings.root)
        ):
            raise Refused("coordinator_separate_test_witness_required")
        gate = Gate(settings)
        if gate.version != 2:
            raise Refused("coordinator_v2_required")
        with _lock(gate.root, LOCK, timeout=2):
            rows = _read(gate.root, version=2)
            doc = Enrollment(
                witness_path=witness.path,
                witness_id=witness.witness_id,
                root_id=root_identity(gate.root),
            )
            witness.provision(doc.root_id, rows)
            fd = os.open(
                gate.root / ENROLLMENT,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
            )
            try:
                data = canonical(doc.model_dump(mode="json"))
                if os.write(fd, data) != len(data):
                    raise Refused("coordinator_enrollment_write_incomplete")
                os.fsync(fd)
            finally:
                os.close(fd)
            fd = _fd(gate.root, SESSION_LOCK, create=True)
            os.close(fd)
            fd = os.open(gate.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)

    @contextmanager
    def session(self, plan, action: Action, *, recover=False, lease_seconds=60):
        if (
            action not in {"deploy", "rollback", "recover", "resume"}
            or not 0 < lease_seconds <= 300
        ):
            raise Refused("coordinator_bounded_session_required")
        plan = snapshot(plan, PlanV2, 65536)
        with _lock(self.root, SESSION_LOCK) as fd:
            doc = enrollment(self.root)
            if doc is None or (doc.witness_path, doc.witness_id) != (
                self.witness.path,
                self.witness.witness_id,
            ):
                raise Refused("coordinator_witness_binding_changed")
            with _lock(self.root, LOCK, timeout=2):
                rows = _read(self.root, version=2)
                previous = self.witness.read(doc.root_id)
                previous.check_journal(rows, exact=previous.session_id is None)
                if previous.session_id is not None and not recover:
                    raise Refused("coordinator_explicit_orphan_recovery_required")
                if recover and action not in {"recover", "rollback"}:
                    raise Refused("coordinator_recovery_action_required")
                current = previous.model_copy(
                    update=dict(
                        revision=previous.revision + 1,
                        epoch=previous.epoch + 1,
                        session_id=secrets.token_hex(32),
                        status="active",
                        expires_at=float(self.clock() + lease_seconds),
                        grant_id=None,
                        grant_sha256=None,
                        sequence=len(rows),
                        journal_sha256=rows[-1]["sha256"],
                    )
                )
                current = self.witness.cas(previous, current)
            session = _Session(self, fd, current, plan, action, recover)
            try:
                yield session
            finally:
                session.active = False
                # No implicit witness release, journal repair, resume or retry.


class _GuardedGate(Gate):
    def __init__(self, session):
        super().__init__(session.owner.settings)
        self.session = session

    def _approval(self, plan, approval, action):
        super()._approval(plan, approval, action)
        self.session.check()
        if (plan.digest, approval.model_dump_json(), action) != (
            self.session.plan.digest,
            self.session.approval.model_dump_json(),
            self.session.action,
        ):
            raise Refused("coordinator_gate_approval_binding_changed")
        self.session.sync()


class _Session:
    def __init__(self, owner, fd, anchor, plan, action, recover):
        self.owner, self.fd, self.anchor = owner, fd, anchor
        self.plan, self.action, self.recover = plan, action, recover
        self.pid = os.getpid()
        self.active, self.used = True, False
        self.challenge = self.grant = self.approval = None
        self.observations = 0
        self.effect_applied = False
        self.baseline = None
        self.gate = _GuardedGate(self)

    def lease(self):
        if (
            not self.active
            or self.pid != os.getpid()
            or not self.owner.clock() < self.anchor.expires_at
        ):
            raise Refused("coordinator_session_expired")
        try:
            actual = os.fstat(self.fd)
            path = (self.owner.root / SESSION_LOCK).stat()
            if (actual.st_dev, actual.st_ino, actual.st_nlink) != (
                path.st_dev,
                path.st_ino,
                1,
            ):
                raise Refused("coordinator_owner_lock_replaced")
            try:
                with _lock(self.owner.root, SESSION_LOCK):
                    raise Refused("coordinator_owner_lock_lost")
            except Busy:
                pass
        except OSError:
            raise Refused("coordinator_owner_lock_lost") from None
        if self.owner.witness.read(self.anchor.root_id) != self.anchor:
            raise Refused("coordinator_fencing_token_stale")
        if root_identity(self.owner.root) != self.anchor.root_id:
            raise Refused("coordinator_root_changed")

    def sync(self):
        self.lease()
        rows = _read(self.owner.root, version=2)
        self.anchor.check_journal(rows)
        if self.anchor.sequence != len(rows):
            if self.grant and any(
                r["operation"] != self.grant.grant_id
                for r in rows[self.anchor.sequence :]
            ):
                raise Refused("coordinator_foreign_journal_operation")
            updated = self.anchor.model_copy(
                update=dict(
                    revision=self.anchor.revision + 1,
                    sequence=len(rows),
                    journal_sha256=rows[-1]["sha256"],
                )
            )
            self.anchor = self.owner.witness.cas(self.anchor, updated)
        return rows

    def observe(self):
        self.lease()
        self.observations += 1
        if self.observations > 8:
            raise Refused("coordinator_observation_budget")
        try:
            value = self.owner.evidence(
                self.plan, self.owner.driver.scope, self.owner.driver.generation
            )
            if type(value) is Capture:
                if value.mode != "simulated":
                    raise ValueError()
                value = value.gate_fixture()
            value = snapshot(value, ObservationV2)
            target = self.owner.driver.scope == self.plan.operation.target
            value.check(
                self.plan,
                target=target,
                require_health=self.action != "rollback" or target,
            )
            if (
                self.baseline is not None
                and not self.effect_applied
                and (value.container_id, value.binding) != self.baseline[1:]
            ):
                raise ValueError()
            return value
        except Exception:
            raise Refused("coordinator_fresh_offline_evidence_required") from None

    def request(self):
        if self.challenge is not None or self.used:
            raise Refused("coordinator_challenge_already_issued")
        rows = self.sync()
        try:
            self.gate._idle()
        except Busy:
            pass  # Known queued/running work must drain after authorization.
        observed = self.observe()
        self.baseline = (
            self.owner.driver.calls,
            observed.container_id,
            observed.binding,
        )
        now = float(self.owner.clock())
        self.challenge = Challenge(
            session_id=self.anchor.session_id,
            epoch=self.anchor.epoch,
            root_id=self.anchor.root_id,
            action=self.action,
            resource_id=self.plan.resource_id,
            server_id=self.plan.operation.current.server_uuid,
            environment_id=self.plan.operation.current.environment_uuid,
            plan_sha256=self.plan.digest,
            runtime_scope_sha256=self.plan.operation.runtime_scope_sha256,
            sequence=len(rows),
            journal_sha256=rows[-1]["sha256"],
            instance_sha256=observed.container_id,
            evidence_sha256=fingerprint(observed),
            created_at=now,
            expires_at=min(self.anchor.expires_at, now + 300),
        )
        return self.challenge

    def check(self):
        self.lease()
        if self.grant is None:
            raise Refused("coordinator_external_operator_grant_required")
        try:
            verified = self.owner.verifier.verify(self.envelope)
            if (
                type(verified) is not OperatorGrant
                or verified != self.grant
                or verified != self.envelope.grant
                or verified.challenge != self.challenge
                or verified.role != "operator"
                or not self.challenge.created_at
                <= verified.issued_at
                <= self.owner.clock()
                < verified.expires_at
                <= self.challenge.expires_at
            ):
                raise ValueError()
        except Exception:
            raise Refused("coordinator_operator_grant_unverified") from None

    def execute(self, envelope, *, drain_timeout=5):
        if self.used or self.challenge is None:
            raise Refused("coordinator_single_action_required")
        self.used = True
        self.envelope = snapshot(envelope, SignedGrant, 65536)
        try:
            self.grant = snapshot(
                self.owner.verifier.verify(self.envelope), OperatorGrant, 65536
            )
        except Exception:
            raise Refused("coordinator_operator_grant_unverified") from None
        self.check()
        self.approval = ApprovalV2(
            approval_id=self.grant.grant_id,
            approved_by=self.grant.subject,
            action=self.action,
            plan_sha256=self.plan.digest,
            runtime_scope_sha256=self.plan.operation.runtime_scope_sha256,
            approved_at=self.grant.issued_at,
            expires_at=self.grant.expires_at,
            confirmed=True,
        )
        with _lock(self.owner.root, LOCK, timeout=2):
            rows = self.sync()
            self.anchor = self.owner.witness.cas(
                self.anchor,
                self.anchor.model_copy(
                    update=dict(
                        revision=self.anchor.revision + 1,
                        grant_id=self.grant.grant_id,
                        grant_sha256=fingerprint(self.envelope),
                    )
                ),
                consume=(self.grant.grant_id, fingerprint(self.envelope)),
            )
            if self.recover and rows[-1]["phase"] in {
                "open",
                "draining",
                "deploying",
                "verifying",
            }:
                old_plan = PlanV2.model_validate(rows[-1]["plan"])
                old_approval = (
                    ApprovalV2.model_validate(rows[-1]["approval"])
                    if rows[-1]["approval"]
                    else None
                )
                _append(
                    self.owner.root,
                    rows,
                    "recovery",
                    rows[-1]["operation"],
                    old_plan,
                    "coordinator_operator_approved_orphan_hold",
                    old_approval,
                )
                # This historical freeze belongs to the interrupted operation.
                self.anchor = self.owner.witness.cas(
                    self.anchor,
                    self.anchor.model_copy(
                        update=dict(
                            revision=self.anchor.revision + 1,
                            sequence=len(rows) + 1,
                            journal_sha256=_read(self.owner.root, version=2)[-1][
                                "sha256"
                            ],
                        )
                    ),
                )
        bridge = _Bridge(self)
        try:
            if self.action in {"deploy", "rollback"}:
                self.gate.run(
                    self.plan, self.approval, bridge, drain_timeout=drain_timeout
                )
            else:
                self.gate.release(
                    self.plan, self.approval, bridge, recovery=self.action == "recover"
                )
            with _lock(self.owner.root, LOCK, timeout=2):
                self.check()
                rows = self.sync()
                self.anchor = self.owner.witness.cas(
                    self.anchor,
                    self.anchor.model_copy(
                        update=dict(
                            revision=self.anchor.revision + 1,
                            status="released" if self.action == "resume" else "held",
                            session_id=None,
                            expires_at=0.0,
                        )
                    ),
                )
            return dict(
                status="verified_offline",
                phase=rows[-1]["phase"],
                admissions="open" if self.action == "resume" else "closed",
                production_release="blocked",
                deployment_permitted=False,
                session_id=self.challenge.session_id,
                epoch=self.challenge.epoch,
            )
        except Exception:
            # Gate may have written recovery. Keep external fence ACTIVE/CLAIMED;
            # read guards remain closed even if journal recording also failed.
            raise


@dataclass
class _Permit:
    session: _Session
    gate_permit: object
    claimed: bool = False

    def check(self):
        if not self.claimed or self.session.anchor.status != "claimed":
            raise Refused("coordinator_claim_required")
        self.session.check()
        self.gate_permit.check()

    def claim(self):
        if self.claimed:
            raise Refused("coordinator_permit_replay")
        self.session.check()
        if self.session.anchor.status != "active":
            raise Refused("coordinator_permit_already_burned")
        with _lock(self.session.owner.root, LOCK, timeout=2):
            self.session.sync()
            self.session.anchor = self.session.owner.witness.cas(
                self.session.anchor,
                self.session.anchor.model_copy(
                    update=dict(
                        revision=self.session.anchor.revision + 1, status="claimed"
                    )
                ),
            )
            self.claimed = True  # Durable burn precedes underlying Gate claim.
        self.gate_permit.claim()
        self.session.check()


class _Bridge:
    def __init__(self, session):
        self.session = session

    def observe(self, plan):
        self.session.check()
        self.session.sync()
        return self.session.observe()

    def deploy(self, plan, permit):
        receipt = self.session.owner.driver.change(plan, _Permit(self.session, permit))
        receipt = snapshot(receipt, DriverReceipt)
        if (
            receipt.session_id,
            receipt.epoch,
            receipt.plan_sha256,
            receipt.grant_id,
            receipt.status,
        ) != (
            self.session.challenge.session_id,
            self.session.challenge.epoch,
            plan.digest,
            self.session.grant.grant_id,
            "completed",
        ):
            raise Refused("coordinator_driver_outcome_uncertain")
        self.session.effect_applied = True
