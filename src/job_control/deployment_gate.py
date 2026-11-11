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
    return hashlib.sha256(canonical(settings.model_dump(mode="json"))).hexdigest()


def require_existing_queue(settings):
    """An enabled gate must never bootstrap a replacement queue on a wrong mount."""
    if settings.deployment_gate_required:
        try:
            root = private(settings.root, directory=True)
            with database(root):
                pass
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


def _read(root):
    fd = _fd(root, JOURNAL)
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
            row = json.loads(line)
        except (ValueError, TypeError, RecursionError):
            raise Blocked("gate_journal_invalid") from None
        if not isinstance(row, dict) or "sha256" not in row:
            raise Blocked("gate_journal_invalid")
        checksum = row.pop("sha256")
        if (
            set(row)
            != {
                "sequence",
                "previous",
                "at",
                "phase",
                "operation",
                "plan",
                "reason",
                "approval",
            }
            or type(row["sequence"]) is not int
            or row["sequence"] != len(rows) + 1
            or row["previous"] != previous
            or checksum != hashlib.sha256(canonical(row)).hexdigest()
            or not isinstance(row["phase"], str)
            or row["phase"] not in PHASES
            or len(rows) >= MAX_EVENTS
        ):
            raise Blocked("gate_journal_invalid")
        if row["plan"] is not None:
            Plan.model_validate(row["plan"])
        if row["approval"] is not None:
            Approval.model_validate(row["approval"])
        row["sha256"] = checksum
        previous = checksum
        rows.append(row)
    return rows


def _append(root, rows, phase, operation, plan, reason, approval=None):
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
    row["sha256"] = hashlib.sha256(canonical(row)).hexdigest()
    data = canonical(row) + b"\n"
    fd = _fd(root, JOURNAL)
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


@contextmanager
def admission(settings):
    root = settings.root
    if not settings.deployment_gate_required and not safe_path(root, JOURNAL).exists():
        yield
        return
    fd = None
    try:
        fd = _fd(root, LOCK)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if _read(root)[-1]["phase"] != "open":
            raise Blocked("deployment_drain_admissions_closed")
    except (OSError, ValueError, KeyError, Blocked) as error:
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
    if not settings.deployment_gate_required and not safe_path(root, JOURNAL).exists():
        yield True
        return
    allowed = False
    fd = None
    try:
        fd = _fd(root, LOCK)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        allowed = _read(root)[-1]["phase"] in {"open", "draining"}
    except (OSError, ValueError, KeyError, Blocked):
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
        return None
    with _lock(settings.root, LOCK):
        _read(settings.root)
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

    def initialize(self):
        """Explicit bootstrap only. Does not open admissions or initialize a DB."""
        if any(
            safe_path(self.root, name).exists()
            for name in (JOURNAL, LOCK, OWNER, WORKER)
        ):
            raise Blocked("existing_gate_requires_manual_recovery")
        with (
            fence(self.root),
            _lock(self.root, OWNER, create=True),
            _lock(self.root, LOCK, create=True),
        ):
            with database(self.root):
                pass
            path = safe_path(self.root, JOURNAL)
            fd = os.open(
                path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
            )
            os.close(fd)
            _append(self.root, [], "held", None, None, "initialized_closed")
            fd = os.open(self.root, os.O_DIRECTORY | os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)

    def status(self):
        """Read-only: no Store construction, lock/file creation or heartbeat write."""
        try:
            with _lock(self.root, LOCK):
                rows = _read(self.root)
                return dict(
                    status="blocked" if rows[-1]["phase"] != "open" else "open",
                    phase=rows[-1]["phase"],
                    sequence=len(rows),
                )
        except (OSError, ValueError, KeyError, Blocked, sqlite3.Error):
            return dict(status="blocked", phase="unknown")

    def _approval(self, plan, approval, action):
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
            rows = _read(self.root)
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
            rows = _read(self.root)
            state = rows[-1]
            plan = Plan.model_validate(state["plan"]) if state["plan"] else None
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
                self._observe(
                    driver, plan, target=False, require_health=action != "rollback"
                )
                with _lock(self.root, LOCK, timeout=2):
                    self._approval(plan, approval, action)
                    rows = _read(self.root)
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
                                _read(self.root),
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
                if before.container_id == after.container_id:
                    raise Blocked("replacement_instance_not_verified")
                with _lock(self.root, LOCK, timeout=2):
                    self._idle()
                    self._approval(plan, approval, action)
                    _append(
                        self.root,
                        _read(self.root),
                        "verified",
                        approval.approval_id,
                        plan,
                        "live_checks_passed_admissions_held",
                        approval,
                    )
                return dict(
                    status="verified", admissions="closed", production_release="blocked"
                )
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
            observed = self._observe(driver, plan, target=True)
            with _lock(self.root, LOCK, timeout=2):
                rows = _read(self.root)
                allowed = (
                    {"recovery", "draining", "deploying", "verifying"}
                    if recovery
                    else {"held", "verified"}
                )
                if rows[-1]["phase"] not in allowed or any(
                    r["operation"] == approval.approval_id for r in rows
                ):
                    raise Blocked("explicit_verified_release_required")
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
