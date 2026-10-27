"""Single-host deployment fence over the existing C16 queue, without DB migration.

The journal is both durable state and a bounded hash-linked audit trail. A torn
record, missing required journal or lost coordinator never opens admissions.
Drivers are explicit adapters, not commands supplied by API callers. This module
contains no Docker, SSH, Coolify client, credentials or network transport.
"""

import fcntl
import hashlib
import json
import logging
import os
import sqlite3
import stat
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import Field, StrictBool

from src.job_control.catalog import safe_path
from src.job_control.models import TERMINAL, Contract, Identifier, Job, canonical
from src.job_control.operations import database, fence, private
from src.job_control.store import Unavailable

JOURNAL = "deployment-gate.v1.jsonl"
JOURNAL_V2 = "deployment-gate.v2.jsonl"
LOCK = ".deployment-admission.lock"
OWNER = ".deployment-owner.lock"
WORKER = ".deployment-worker.lock"
MAX_BYTES = 1024 * 1024
MAX_EVENTS = 1024
SHA = r"^[a-f0-9]{40}$"
DIGEST = r"^[a-f0-9]{64}$"
IMAGE = (
    r"^[A-Za-z0-9][A-Za-z0-9._:-]*(/[A-Za-z0-9][A-Za-z0-9._:-]*)*@sha256:[a-f0-9]{64}$"
)
PHASES = {"held", "open", "draining", "deploying", "verifying", "verified", "recovery"}


class Blocked(Unavailable):
    """Fixed reason codes only; no config, remote responses or secrets."""


class Busy(Blocked):
    pass


class Plan(Contract):
    resource_id: Identifier
    role: Literal["ui", "api", "worker"]
    current_sha: str = Field(pattern=SHA)
    current_image: str = Field(pattern=IMAGE)
    target_sha: str = Field(pattern=SHA)
    target_image: str = Field(pattern=IMAGE)
    settings_sha256: str = Field(pattern=DIGEST)
    persistence_sha256: str = Field(pattern=DIGEST)
    protected_resources_sha256: str = Field(pattern=DIGEST)

    @property
    def digest(self):
        return hashlib.sha256(canonical(self.model_dump(mode="json"))).hexdigest()


class Approval(Contract):
    approval_id: Identifier
    approved_by: Identifier
    action: Literal["deploy", "rollback", "recover", "resume"]
    plan_sha256: str = Field(pattern=DIGEST)
    approved_at: float = Field(allow_inf_nan=False, strict=True)
    expires_at: float = Field(allow_inf_nan=False, strict=True)
    confirmed: StrictBool

    def check(self, plan, action):
        current = time.time()
        if not (
            self.confirmed
            and self.action == action
            and self.plan_sha256 == plan.digest
            and self.approved_at <= current < self.expires_at
            and 0 < self.expires_at - self.approved_at <= 3600
        ):
            raise Blocked("approval_missing_expired_or_mismatched")


class Observation(Contract):
    """Must come from a live driver inspection, never from a cached health file."""

    resource_id: Identifier
    revision: str = Field(pattern=SHA)
    image: str = Field(pattern=IMAGE)
    container_id: Identifier
    observed_at: float = Field(allow_inf_nan=False, strict=True)
    healthy: StrictBool
    ready: StrictBool
    triggers_disabled: StrictBool
    single_resource_change: StrictBool
    gate_protocol: Literal["c26-gate-v1"]
    external_jobs_idle: StrictBool
    external_intake_fenced: StrictBool
    settings_sha256: str = Field(pattern=DIGEST)
    persistence_sha256: str = Field(pattern=DIGEST)
    protected_resources_sha256: str = Field(pattern=DIGEST)


class Driver(Protocol):
    def observe(self, plan: Plan) -> Observation: ...

    def deploy(self, plan: Plan, permit: "Permit") -> None: ...


def settings_digest(settings):
    data = settings.model_dump(mode="json")
    if data.get("coordinator_test_required") is False:
        data.pop("coordinator_test_required")
    # Preserve byte-for-byte v1 hash semantics for pre-C26-D configurations.
    if data.get("deployment_gate_protocol") == "c26-gate-v1":
        data.pop("deployment_gate_protocol")
    return hashlib.sha256(canonical(data)).hexdigest()


def selected_version(settings):
    protocol = getattr(settings, "deployment_gate_protocol", "c26-gate-v1")
    if protocol not in {"c26-gate-v1", "c26-gate-v2"}:
        raise Blocked("unknown_gate_protocol")
    if protocol == "c26-gate-v2" and not settings.deployment_gate_required:
        raise Blocked("v2_mandatory_gate_required")
    return 2 if protocol == "c26-gate-v2" else 1


def journal_present(root):
    return any(safe_path(root, name).exists() for name in (JOURNAL, JOURNAL_V2))


def journal_name(root, version=None):
    found = [
        v
        for v, name in ((1, JOURNAL), (2, JOURNAL_V2))
        if safe_path(root, name).exists()
    ]
    if len(found) > 1 or found and version is not None and found != [version]:
        raise Blocked("gate_journal_protocol_mismatch")
    version = version or (found[0] if found else 1)
    return JOURNAL_V2 if version == 2 else JOURNAL


def require_existing_queue(settings):
    """An enabled gate must never bootstrap a replacement queue on a wrong mount."""
    if settings.deployment_gate_required:
        try:
            root = private(settings.root, directory=True)
            with database(root):
                pass
            if selected_version(settings) == 2:
                _read(root, version=2)
        except (OSError, ValueError, sqlite3.Error):
            raise Blocked("existing_private_c16_queue_required") from None


def _fd(root, name, *, create=False):
    path = safe_path(root, name)
    fd = os.open(
        path,
        os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | (os.O_CREAT if create else 0),
        0o600,
    )
    try:
        info = os.fstat(fd)
        if not (
            stat.S_ISREG(info.st_mode)
            and info.st_uid == os.geteuid()
            and stat.S_IMODE(info.st_mode) == 0o600
            and info.st_nlink == 1
        ):
            raise Blocked("private_gate_file_required")
    except BaseException:
        os.close(fd)
        raise
    return fd


@contextmanager
def _lock(root, name, *, create=False, shared=False, timeout=0):
    if not 0 <= timeout <= 2:
        raise ValueError("Bounded gate lock wait required")
    fd = _fd(root, name, create=create)
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(
                    fd, (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB
                )
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    if name == OWNER:
                        logging.getLogger(__name__).warning("deployment_gate_lock_busy")
                    raise Busy("gate_lock_busy") from None
                time.sleep(0.005)
        yield fd
    finally:
        os.close(fd)


def _unique_json(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("Duplicate journal field")
        data[key] = value
    return data


def _read(root, *, version=None):
    name = journal_name(root, version)
    version = 2 if name == JOURNAL_V2 else 1
    fd = _fd(root, name)
    try:
        data = os.read(fd, MAX_BYTES + 1)
    finally:
        os.close(fd)
    if not data or len(data) > MAX_BYTES or not data.endswith(b"\n"):
        raise Blocked("gate_journal_incomplete_or_full")
    rows = []
    previous = "0" * 64
    for line in data.splitlines():
        try:
            row = (
                json.loads(line, object_pairs_hook=_unique_json)
                if version == 2
                else json.loads(line)
            )
        except (ValueError, TypeError, RecursionError):
            raise Blocked("gate_journal_invalid") from None
        if not isinstance(row, dict) or "sha256" not in row:
            raise Blocked("gate_journal_invalid")
        checksum = row.pop("sha256")
        if (
            set(row)
            != (
                {
                    "sequence",
                    "previous",
                    "at",
                    "phase",
                    "operation",
                    "plan",
                    "reason",
                    "approval",
                }
                | (
                    {"schema_version", "protocol", "mode", "runtime_scope_sha256"}
                    if version == 2
                    else set()
                )
            )
            or type(row["sequence"]) is not int
            or row["sequence"] != len(rows) + 1
            or row["previous"] != previous
            or checksum != hashlib.sha256(canonical(row)).hexdigest()
            or not isinstance(row["phase"], str)
            or row["phase"] not in PHASES
            or len(rows) >= MAX_EVENTS
        ):
            raise Blocked("gate_journal_invalid")
        if version == 2:
            from src.job_control.deployment_scope import JournalEventV2

            JournalEventV2.model_validate(row | {"sha256": checksum})
        else:
            if row["plan"] is not None:
                Plan.model_validate(row["plan"])
            if row["approval"] is not None:
                Approval.model_validate(row["approval"])
        row["sha256"] = checksum
        previous = checksum
        rows.append(row)
    return rows


def _append(root, rows, phase, operation, plan, reason, approval=None, *, version=None):
    version = version or (rows[0].get("schema_version", 1) if rows else 1)
    row = dict(
        sequence=len(rows) + 1,
        previous=rows[-1]["sha256"] if rows else "0" * 64,
        at=time.time(),
        phase=phase,
        operation=operation,
        plan=plan.model_dump(mode="json") if plan else None,
        reason=reason,
        approval=approval.model_dump(mode="json") if approval else None,
    )
    if version == 2:
        row.update(
            schema_version=2,
            protocol="c26-gate-v2",
            mode="offline_fixture",
            runtime_scope_sha256=plan.operation.runtime_scope_sha256 if plan else None,
        )
    row["sha256"] = hashlib.sha256(canonical(row)).hexdigest()
    if version == 2:
        from src.job_control.deployment_scope import JournalEventV2

        JournalEventV2.model_validate(row)
    data = canonical(row) + b"\n"
    fd = _fd(root, journal_name(root, version))
    try:
        if len(rows) >= MAX_EVENTS or os.fstat(fd).st_size + len(data) > MAX_BYTES:
            raise Blocked("gate_audit_capacity")
        os.lseek(fd, 0, os.SEEK_END)
        if os.write(fd, data) != len(data):
            raise Blocked("gate_audit_write_incomplete")
        os.fsync(fd)
    finally:
        os.close(fd)
    return rows + [row]


def _settings_bound(settings, rows):
    """Every v2 writer must use exactly the settings authorized at resume.

    Store writers receive the digest from their owning Controller/Executor;
    a bare Store has no authority to infer settings from a journal or a file.
    V1 retains its published compatibility contract.
    """
    if selected_version(settings) != 2:
        return True
    expected = (rows[-1].get("plan") or {}).get("settings_sha256")
    actual = (
        settings_digest(settings)
        if hasattr(settings, "model_dump")
        else getattr(settings, "gate_settings_sha256", None)
    )
    return expected is not None and actual == expected


@contextmanager
def admission(settings):
    root = settings.root
    if (
        not settings.deployment_gate_required
        and not journal_present(root)
        and not safe_path(root, "coordinator-test-enrollment.v1.json").exists()
        and not getattr(settings, "coordinator_test_required", False)
    ):
        yield
        return
    fd = None
    try:
        fd = _fd(root, LOCK)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rows = _read(root, version=selected_version(settings))
        from src.job_control.coordinator_state import guard

        if (
            rows[-1]["phase"] != "open"
            or not _settings_bound(settings, rows)
            or not guard(
                root,
                rows,
                required=getattr(settings, "coordinator_test_required", False),
            )
        ):
            raise Blocked("deployment_drain_admissions_closed")
    except (OSError, ValueError, KeyError, Unavailable, sqlite3.Error) as error:
        if fd is not None:
            os.close(fd)
        raise Blocked("deployment_gate_unavailable") from error
    try:
        yield
    finally:
        os.close(fd)


@contextmanager
def dispatch(settings):
    """A damaged gate pauses dispatch; existing children keep running/being reaped."""
    root = settings.root
    if (
        not settings.deployment_gate_required
        and not journal_present(root)
        and not safe_path(root, "coordinator-test-enrollment.v1.json").exists()
        and not getattr(settings, "coordinator_test_required", False)
    ):
        yield True
        return
    allowed = False
    fd = None
    try:
        fd = _fd(root, LOCK)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rows = _read(root, version=selected_version(settings))
        from src.job_control.coordinator_state import guard

        allowed = (
            rows[-1]["phase"] in {"open", "draining"}
            and _settings_bound(settings, rows)
            and guard(
                root,
                rows,
                dispatch=True,
                required=getattr(settings, "coordinator_test_required", False),
            )
        )
    except (OSError, ValueError, KeyError, Unavailable, sqlite3.Error):
        if fd is not None:
            os.close(fd)
            fd = None
    try:
        yield allowed
    finally:
        if fd is not None:
            os.close(fd)


def register_worker(settings):
    if not settings.deployment_gate_required:
        if journal_present(settings.root):
            _read(settings.root, version=selected_version(settings))
        return None
    with _lock(settings.root, LOCK):
        _read(settings.root, version=selected_version(settings))
        fd = _fd(settings.root, WORKER, create=True)
        try:
            fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BaseException:
            os.close(fd)
            raise
        return fd


def hold_restored_root(root):
    """Only called for a newly copied isolated C22 restore; preserve audit history."""
    root = private(root, directory=True)
    with _lock(root, OWNER, create=True), _lock(root, LOCK, create=True):
        _append(
            root, _read(root), "held", None, None, "isolated_restore_admissions_held"
        )


@dataclass
class Permit:
    gate: "Gate"
    plan: Plan
    operation: str
    approval: Approval
    active: bool = True

    def check(self):
        if not self.active:
            raise Blocked("expired_deployment_permit")
        with _lock(self.gate.root, LOCK, timeout=2):
            state = _read(self.gate.root)[-1]
            if (
                state["phase"] != "deploying"
                or state["operation"] != self.operation
                or state["plan"] != self.plan.model_dump(mode="json")
            ):
                raise Blocked("stale_deployment_permit")
            self.gate._idle()
            self.gate._approval(self.plan, self.approval, self.approval.action)


class Gate:
    def __init__(self, settings):
        if not settings.deployment_gate_required:
            raise Blocked("explicit_gate_configuration_required")
        self.settings = settings
        self.root = private(settings.root, directory=True)
        self.version = selected_version(settings)
        self._active_permit = None
        self._permit_claimed = False

    def initialize(self):
        """Explicit bootstrap only. Does not open admissions or initialize a DB."""
        if any(
            safe_path(self.root, name).exists()
            for name in (JOURNAL, JOURNAL_V2, LOCK, OWNER, WORKER)
        ):
            raise Blocked("existing_gate_requires_manual_recovery")
        with (
            fence(self.root),
            _lock(self.root, OWNER, create=True),
            _lock(self.root, LOCK, create=True),
        ):
            with database(self.root):
                pass
            path = safe_path(self.root, JOURNAL_V2 if self.version == 2 else JOURNAL)
            fd = os.open(
                path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
            )
            os.close(fd)
            _append(
                self.root,
                [],
                "held",
                None,
                None,
                "initialized_closed",
                version=self.version,
            )
            fd = os.open(self.root, os.O_DIRECTORY | os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)

    def status(self):
        """Read-only: no Store construction, lock/file creation or heartbeat write."""
        try:
            with _lock(self.root, LOCK):
                rows = _read(self.root, version=self.version)
                result = dict(
                    status="blocked" if rows[-1]["phase"] != "open" else "open",
                    phase=rows[-1]["phase"],
                    sequence=len(rows),
                )
                if rows[-1]["phase"] == "open" and not _settings_bound(
                    self.settings, rows
                ):
                    result["status"] = "blocked"
                    result["settings_binding_blocked"] = True
                if (
                    getattr(self.settings, "coordinator_test_required", False)
                    or safe_path(
                        self.root, "coordinator-test-enrollment.v1.json"
                    ).exists()
                ):
                    from src.job_control.coordinator_state import guard

                    if not guard(
                        self.root,
                        rows,
                        required=getattr(
                            self.settings, "coordinator_test_required", False
                        ),
                    ):
                        result["status"] = "blocked"
                        result["coordinator_test_blocked"] = True
                if self.version == 2:
                    result.update(
                        schema_version=2,
                        protocol="c26-gate-v2",
                        mode="offline_fixture",
                        deployment_permitted=False,
                        production_release="blocked",
                    )
                return result
        except (OSError, ValueError, KeyError, Unavailable, sqlite3.Error):
            return dict(status="blocked", phase="unknown")

    def _approval(self, plan, approval, action):
        if (
            getattr(self.settings, "coordinator_test_required", False)
            or safe_path(self.root, "coordinator-test-enrollment.v1.json").exists()
        ):
            from src.job_control.deployment_coordinator import _GuardedGate

            if type(self) is not _GuardedGate:
                raise Blocked("coordinator_session_required")
        if selected_version(self.settings) != self.version:
            raise Blocked("gate_protocol_changed")
        journal_name(self.root, self.version)
        if self.version == 2:
            from src.job_control.deployment_scope import ApprovalV2, PlanV2, snapshot

            plan = snapshot(plan, PlanV2, 65536)
            approval = snapshot(approval, ApprovalV2)
            _read(self.root, version=2)
            root = plan.operation.current.jobroot
            info = self.root.stat()
            if str(self.root) not in {root.source, root.destination} or (
                info.st_dev,
                info.st_ino,
            ) != (root.device, root.inode):
                raise Blocked("v2_coordinator_jobroot_mismatch")
        elif type(plan) is not Plan or type(approval) is not Approval:
            raise Blocked("explicit_v1_plan_and_approval_required")
        if not isinstance(plan, Plan) or not isinstance(approval, Approval):
            raise Blocked("explicit_plan_and_approval_required")
        approval.check(plan, action)
        if plan.settings_sha256 != settings_digest(self.settings):
            raise Blocked("settings_binding_changed")

    def _idle(self):
        """Only under admission lock; prove queue, heartbeat and lifecycle locks."""
        if safe_path(self.root, "quarantine").exists():
            raise Blocked("worker_quarantined")
        try:
            with _lock(self.root, WORKER):
                raise Blocked("gate_aware_worker_absent")
        except Busy:
            pass  # A new gate-aware executor holds its protocol lease.
        try:
            with _lock(self.root, "worker.lock"):
                raise Blocked("executor_absent")
        except Busy:
            pass
        with database(self.root) as db:
            heartbeat = db.execute("SELECT heartbeat FROM worker WHERE id=1").fetchone()
            if (
                not heartbeat
                or not 0 <= time.time() - heartbeat[0] < self.settings.worker_ttl
            ):
                raise Blocked("worker_status_unknown")
            jobs = tuple(
                Job.model_validate_json(r[0])
                for r in db.execute("SELECT data FROM jobs")
            )
        if any(job.status not in TERMINAL for job in jobs):
            raise Busy("jobs_not_terminal")
        for job in jobs:
            path = safe_path(self.root, "jobs/" + job.job_id + "/execution.lock")
            if path.exists():
                with _lock(path.parent, path.name):
                    pass

    def _observe(self, driver, plan, *, target, require_health=True):
        try:
            observed = driver.observe(plan)
        except Exception:
            raise Blocked("deployment_driver_observation_failed") from None
        if self.version == 2:
            from src.job_control.deployment_scope import ObservationV2, snapshot

            return snapshot(observed, ObservationV2).check(
                plan, target=target, require_health=require_health
            )
        if not isinstance(observed, Observation):
            raise Blocked("live_observation_required")
        if not (
            observed.resource_id == plan.resource_id
            and observed.revision == (plan.target_sha if target else plan.current_sha)
            and observed.image == (plan.target_image if target else plan.current_image)
            and 0 <= time.time() - observed.observed_at <= 30
            and (not require_health or observed.healthy and observed.ready)
            and observed.triggers_disabled
            and observed.single_resource_change
            and observed.external_jobs_idle
            and observed.external_intake_fenced
            and observed.settings_sha256 == plan.settings_sha256
            and observed.persistence_sha256 == plan.persistence_sha256
            and observed.protected_resources_sha256 == plan.protected_resources_sha256
        ):
            raise Blocked("live_health_version_scope_or_trigger_check_failed")
        return observed

    def _record(self, phase, approval, plan, reason):
        with _lock(self.root, LOCK, timeout=2):
            rows = _read(self.root, version=self.version)
            return _append(
                self.root,
                rows,
                phase,
                approval.approval_id if approval else None,
                plan,
                reason,
                approval,
            )

    def _refused(self, reason):
        with _lock(self.root, LOCK, timeout=2):
            rows = _read(self.root, version=self.version)
            state = rows[-1]
            if self.version == 2:
                from src.job_control.deployment_scope import PlanV2

                plan_type = PlanV2
            else:
                plan_type = Plan
            plan = plan_type.model_validate(state["plan"]) if state["plan"] else None
            _append(self.root, rows, state["phase"], state["operation"], plan, reason)

    def run(self, plan, approval, driver, *, drain_timeout=60):
        """One coordinator outside replaced containers; driver must check its permit.

        Deploy/rollback never reopens admissions. No automatic lease expiry,
        retry, rollback, queue reconciliation, writer restart or job cancellation.
        """
        if not 0 <= drain_timeout <= 3600:
            raise Blocked("bounded_drain_timeout_required")
        with fence(self.root), _lock(self.root, OWNER):
            permit = None
            started = False
            try:
                action = approval.action if isinstance(approval, Approval) else "deploy"
                if action not in {"deploy", "rollback"}:
                    raise Blocked("deploy_or_rollback_approval_required")
                self._approval(plan, approval, action)
                if self.version == 2:
                    from src.job_control.deployment_scope import (
                        ApprovalV2,
                        PlanV2,
                        snapshot,
                    )

                    plan = snapshot(plan, PlanV2, 65536)
                    approval = snapshot(approval, ApprovalV2)
                self._observe(
                    driver, plan, target=False, require_health=action != "rollback"
                )
                with _lock(self.root, LOCK, timeout=2):
                    self._approval(plan, approval, action)
                    rows = _read(self.root, version=self.version)
                    state = rows[-1]
                    permitted = (
                        state["phase"] == "open"
                        if action == "deploy"
                        else state["phase"] in {"recovery", "verified"}
                    )
                    if not permitted or any(
                        r["operation"] == approval.approval_id for r in rows
                    ):
                        raise Blocked("gate_phase_or_approval_replay")
                    _append(
                        self.root,
                        rows,
                        "draining",
                        approval.approval_id,
                        plan,
                        "operator_approved_drain",
                        approval,
                    )
                    started = True
                deadline = time.monotonic() + drain_timeout
                while True:
                    self._approval(plan, approval, action)
                    try:
                        with _lock(self.root, LOCK, timeout=2):
                            self._idle()
                            _append(
                                self.root,
                                _read(self.root, version=self.version),
                                "deploying",
                                approval.approval_id,
                                plan,
                                "idle_fenced_for_exact_plan",
                                approval,
                            )
                        break
                    except Busy:
                        if time.monotonic() >= deadline:
                            raise Blocked(
                                "drain_timeout_admissions_remain_closed"
                            ) from None
                        time.sleep(0.05)
                # Repeat live scope/trigger/revision inspection immediately before
                # the only deployment call; admissions/dispatch remain closed.
                before = self._observe(
                    driver, plan, target=False, require_health=action != "rollback"
                )
                self._approval(plan, approval, action)
                if self.version == 2:
                    from src.job_control.deployment_scope import PermitV2

                    permit = PermitV2(
                        self, plan, approval.approval_id, approval, driver, before
                    )
                    self._active_permit = (
                        permit,
                        plan.digest,
                        approval.model_dump_json(),
                        approval.approval_id,
                        id(driver),
                        before.container_id,
                        before.binding.model_dump_json(),
                    )
                    self._permit_claimed = False
                else:
                    permit = Permit(self, plan, approval.approval_id, approval)
                permit.check()
                try:
                    driver.deploy(plan, permit)
                except Exception:
                    raise Blocked("deployment_driver_change_failed") from None
                self._record(
                    "verifying", approval, plan, "container_change_requires_live_checks"
                )
                after = self._observe(driver, plan, target=True)
                if self.version == 2:
                    from src.job_control.deployment_scope import replacement

                    if not self._permit_claimed:
                        raise Blocked("v2_driver_did_not_claim_permit")
                    replacement(plan, before, after)
                if before.container_id == after.container_id:
                    raise Blocked("replacement_instance_not_verified")
                with _lock(self.root, LOCK, timeout=2):
                    self._idle()
                    self._approval(plan, approval, action)
                    _append(
                        self.root,
                        _read(self.root, version=self.version),
                        "verified",
                        approval.approval_id,
                        plan,
                        "live_checks_passed_admissions_held",
                        approval,
                    )
                result = dict(
                    status="verified", admissions="closed", production_release="blocked"
                )
                if self.version == 2:
                    result.update(
                        status="verified_offline",
                        mode="offline_fixture",
                        deployment_permitted=False,
                    )
                return result
            except Exception:
                if started:
                    self._record(
                        "recovery",
                        approval,
                        plan,
                        "operation_failed_manual_recovery_required",
                    )
                else:
                    self._refused("deployment_request_refused")
                raise
            finally:
                if permit is not None:
                    permit.active = False
                self._active_permit = None

    def release(self, plan, approval, driver, *, recovery=False):
        try:
            return self._release(plan, approval, driver, recovery=recovery)
        except Exception:
            try:
                self._refused("admission_release_refused")
            except (OSError, ValueError, KeyError, Blocked):
                logging.getLogger(__name__).warning(
                    "deployment_gate_refused_audit_unavailable"
                )
            raise

    def _release(self, plan, approval, driver, *, recovery=False):
        """Explicit fresh observation + new approval; recovery first stays closed."""
        with fence(self.root), _lock(self.root, OWNER):
            action = "recover" if recovery else "resume"
            self._approval(plan, approval, action)
            if self.version == 2:
                from src.job_control.deployment_scope import (
                    ApprovalV2,
                    PlanV2,
                    snapshot,
                )

                plan = snapshot(plan, PlanV2, 65536)
                approval = snapshot(approval, ApprovalV2)
            observed = self._observe(driver, plan, target=True)
            with _lock(self.root, LOCK, timeout=2):
                rows = _read(self.root, version=self.version)
                allowed = (
                    {"recovery", "draining", "deploying", "verifying"}
                    if recovery
                    else {"held", "verified"}
                )
                if rows[-1]["phase"] not in allowed or any(
                    r["operation"] == approval.approval_id for r in rows
                ):
                    raise Blocked("explicit_verified_release_required")
                if self.version == 2:
                    if recovery and rows[-1]["plan"] != plan.model_dump(mode="json"):
                        raise Blocked("v2_recovery_operation_mismatch")
                    if (
                        not recovery
                        and rows[-1]["phase"] == "held"
                        and plan.operation.current != plan.operation.target
                    ):
                        raise Blocked("v2_bootstrap_identical_scope_required")
                if not recovery:
                    if rows[-1]["phase"] == "held":
                        if (
                            plan.current_sha != plan.target_sha
                            or plan.current_image != plan.target_image
                        ):
                            raise Blocked("bootstrap_current_version_required")
                    elif rows[-1]["plan"] != plan.model_dump(mode="json"):
                        raise Blocked("verified_plan_binding_required")
                self._idle()
                self._approval(plan, approval, action)
                if not 0 <= time.time() - observed.observed_at <= 30:
                    raise Blocked("release_observation_expired")
                _append(
                    self.root,
                    rows,
                    "verified" if recovery else "open",
                    approval.approval_id,
                    plan,
                    "recovery_verified_still_held"
                    if recovery
                    else "operator_approved_admission_resume",
                    approval,
                )
        return self.status()
