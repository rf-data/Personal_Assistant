"""One OS operator, one manually approved C16 job. No network authority.

The OS account, installed code, private specs and workspace are the trust boundary.
A process able to write them already has the operator's authority. No SSH env var,
API token, test witness, fixture identity or v2 deployment journal is a grant.
"""

import fcntl
import hashlib
import json
import os
import pwd
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

from pydantic import Field

from src.job_control.catalog import read_file, safe_path, verified_files
from src.job_control.models import (
    TERMINAL,
    Contract,
    Identifier,
    Preview,
    Principal,
    Settings,
    Sha,
    canonical,
    fingerprint,
    load_settings,
)
from src.job_control.operations import database, private
from src.job_control.store import Store, Unavailable
from src.tools_materials.capacity import load_limits
from src.workflows.definition import prepare

PROTOCOL = "c26-native-v1"
MARKER = "native-scope.v1.json"
AUTHORITY = ContextVar("native_manual_authority", default=None)
WORKER = ContextVar("native_single_job", default=None)


class Enrollment(Contract):
    protocol: Literal["c26-native-v1"]
    settings: Settings
    config: Path
    limits: Path
    config_sha256: Sha
    limits_sha256: Sha


class Grant(Contract):
    protocol: Literal["c26-native-v1"]
    nonce: Sha
    job_id: Identifier
    preview: Preview
    binding: Sha
    approved_uid: int = Field(ge=1, strict=True)
    approved_at: int = Field(strict=True)
    expires_at: int = Field(strict=True)


def digest(path):
    return hashlib.sha256(read_file(private(path))).hexdigest()


def write_new(path, value):
    """No overwrite; a partial record blocks use and is retained for investigation."""
    data = canonical(value)
    fd = os.open(
        safe_path(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def native_root(settings):
    return (
        getattr(settings, "deployment_gate_protocol", None) == PROTOCOL
        or safe_path(settings.root, MARKER).exists()
    )


def actor(settings):
    if (
        settings.deployment_gate_protocol != PROTOCOL
        or settings.native_uid != os.getuid()
        or os.geteuid() != os.getuid()
        or os.getuid() == 0
    ):
        raise PermissionError("Enrolled nonprivileged OS operator required")
    pwd.getpwuid(os.getuid())  # Require a real local account, never a supplied subject.
    return Principal(
        subject="uid_" + str(os.getuid()), role="operator", courses=("cs50_python",)
    )


def policy(settings, limits):
    # Revalidate even callers that used model_copy or a bare Store.
    settings = Settings.model_validate(settings.model_dump(mode="json"))
    actor(settings)
    if (
        limits.reserve_bytes < 5 * 1024**3
        or limits.job_bytes > 512 * 1024**2
        or limits.catalog_bytes > 128 * 1024**2
        or limits.max_materials > 3
    ):
        raise ValueError("Restricted native capacity limits required")
    for entry in settings.catalog.values():
        verified_files(entry)
        prepared = prepare(entry)
        from scripts.cs50p_mvp import admit
        from src.model_materials.materials import ArtifactReceipt
        from src.tools_materials.batch import Approvals, SourceApproval

        values = verified_files(entry)
        if (
            not {"raw.source", "approval.json", "download_receipt.v1.json"}
            <= values.keys()
        ):
            raise PermissionError("Sealed reviewed download catalog required")
        receipt = ArtifactReceipt.model_validate_json(
            values["download_receipt.v1.json"]
        )
        approval = SourceApproval.model_validate_json(values["approval.json"])
        if (
            receipt.origin != "http_download"
            or receipt.status != "verified"
            or receipt.raw_sha256 != hashlib.sha256(values["raw.source"]).hexdigest()
            or prepared.definition.sources != {receipt.binding.source_id: "raw.source"}
            or receipt.binding.source_origin != prepared.definition.source_origin
            or (
                approval.expected_sha256 is not None
                and approval.expected_sha256 != receipt.raw_sha256
            )
        ):
            raise PermissionError(
                "Download provenance/hash differs from native catalog"
            )
        admit(
            SimpleNamespace(materials=(receipt.binding,)),
            limits,
            Approvals(sources=(approval,)),
        )
        if (
            settings.native_mode == "ssh-runtime"
            and prepared.definition.source_origin != "official"
        ):
            raise PermissionError("Synthetic material is offline-test only")
        if any(
            b.resource.course_id != "cs50_python" or b.format not in {"html", "pdf"}
            for b in prepared.plan.materials
            if b.source_id in prepared.definition.sources
        ):
            raise PermissionError("Only CS50P HTML/PDF inputs admitted")


def enrolled(settings, *, verify_queue=True):
    private(settings.root, directory=True)
    record = Enrollment.model_validate_json(read_file(private(settings.root / MARKER)))
    if (
        record.protocol != PROTOCOL
        or settings.deployment_gate_protocol != PROTOCOL
        or record.settings != settings
        or record.config_sha256 != digest(record.config)
        or record.limits_sha256 != digest(record.limits)
        or load_settings(record.config) != settings
    ):
        raise PermissionError("Native enrollment/configuration changed")
    for name in (
        "deployment-gate.v1.jsonl",
        "deployment-gate.v2.jsonl",
        "coordinator-test-enrollment.v1.json",
        "quarantine",
    ):
        if safe_path(settings.root, name).exists():
            raise PermissionError("Foreign gate or quarantined workspace")
    policy(settings, load_limits(private(record.limits)))
    if verify_queue:
        with database(settings.root):
            pass
    else:
        path = private(settings.root / "jobs.sqlite3")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            header = os.pread(fd, 100, 0)
        finally:
            os.close(fd)
        if (
            header[:16] != b"SQLite format 3\x00"
            or int.from_bytes(header[60:64], "big") != 1
        ):
            raise ValueError("C16 queue header/schema version invalid")
    return record


@contextmanager
def lock(root):
    path = safe_path(root, ".native-admission.lock")
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        private(path)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def initialize(config, limits_path):
    from src.job_control.operations import preflight

    limits = load_limits(private(limits_path))
    settings = preflight(config, min_free_bytes=limits.reserve_bytes)
    policy(settings, limits)
    # Explicit bootstrap only, never adopt an existing queue, gate or unknown data.
    if any(settings.root.iterdir()):
        raise PermissionError("Empty private native workspace required")
    record = Enrollment(
        protocol=PROTOCOL,
        settings=settings,
        config=private(config),
        limits=private(limits_path),
        config_sha256=digest(config),
        limits_sha256=digest(limits_path),
    )
    Store(settings.root)
    (settings.root / "native-grants").mkdir(mode=0o700)
    write_new(settings.root / MARKER, record.model_dump(mode="json"))
    return record.model_dump(mode="json")


def binding(settings, preview):
    record = enrolled(settings)
    # Installed code is part of the approval; no reuse across code changes.
    repo = Path(__file__).resolve().parents[2]
    code = {
        str(p.relative_to(repo)): hashlib.sha256(read_file(p)).hexdigest()
        for folder in (repo / "src", repo / "scripts")
        for p in sorted(folder.rglob("*.py"))
    }
    entry = settings.catalog[preview.input_refs[0]]
    verified_files(entry)
    return fingerprint(
        dict(
            enrollment=record.model_dump(mode="json"),
            preview=preview.model_dump(mode="json"),
            code=code,
        )
    )


def review(settings, source_ref, workflow_id, *, resume=False):
    from src.job_control.catalog import prepare_indexes, resolve_preview
    from src.job_control.models import PreviewRequest
    from src.workflows.service import inspect

    enrolled(settings)
    user = actor(settings)
    report, _, current = inspect(settings, user, source_ref, workflow_id)
    if current and (
        not resume or current.status not in TERMINAL or current.status == "completed"
    ):
        raise PermissionError(
            "Resume requires a failed/cancelled/interrupted predecessor"
        )
    preview, _ = resolve_preview(
        settings,
        PreviewRequest(
            process_id="cs50_offline_workflow",
            parameters=dict(
                source_ref=source_ref,
                course_id="cs50_python",
                workflow_id=workflow_id,
                previous_run_id=current.job_id if current else None,
            ),
        ),
        user,
        prepare_indexes(settings),
    )
    value = dict(
        preview=preview.model_dump(mode="json"),
        binding=binding(settings, preview),
        report=report.model_dump(mode="json"),
        uid=os.getuid(),
    )
    value["review_id"] = fingerprint(value)
    return value


def create_guard(settings, user, request, key):
    if not native_root(settings):
        return
    enrolled(settings)
    auth = AUTHORITY.get()
    if (
        auth is None
        or user != actor(settings)
        or request.start
        or request.preview != auth["preview"]
        or key != auth["key"]
    ):
        raise PermissionError("Exact manual native admission required")


def start_guard(settings, job):
    if native_root(settings):
        worker_guard(settings)
        job_guard(settings, job)


@contextmanager
def admission(settings):
    # Bare Store queued transitions cannot manufacture native authority.
    auth = AUTHORITY.get()
    if not hasattr(settings, "model_dump"):
        if auth is None or settings.root != auth["settings"].root:
            raise PermissionError(
                "Native Store admission needs scoped controller authority"
            )
        settings = auth["settings"]
    enrolled(settings)
    if auth is None or auth["settings"] != settings:
        raise PermissionError("Manual native admission required")
    yield


def approve(settings, source_ref, workflow_id, review_id, *, ttl=300, resume=False):
    from src.job_control.controller import Controller

    if type(ttl) is not int or not 1 <= ttl <= 600:
        raise ValueError("Grant lifetime must be 1..600 seconds")
    with lock(settings.root):
        value = review(settings, source_ref, workflow_id, resume=resume)
        if review_id != value["review_id"]:
            raise PermissionError("Review changed")
        with database(settings.root) as db:
            if any(
                json.loads(r[0])["status"] not in TERMINAL
                for r in db.execute("SELECT data FROM jobs")
            ):
                raise Unavailable("One active job maximum, including pending approvals")
        preview = Preview.model_validate(value["preview"])
        nonce = fingerprint(uuid.uuid4().hex)
        auth = dict(settings=settings, preview=preview, key="native_" + nonce[:48])
        token = AUTHORITY.set(auth)
        try:
            job = Controller(settings).create(
                actor(settings),
                dict(
                    preview=preview.model_dump(mode="json"), confirmed=True, start=False
                ),
                auth["key"],
            )
            now = int(time.time())
            grant = Grant(
                protocol=PROTOCOL,
                nonce=nonce,
                job_id=job.job_id,
                preview=preview,
                binding=value["binding"],
                approved_uid=os.getuid(),
                approved_at=now,
                expires_at=now + ttl,
            )
            write_new(
                settings.root / "native-grants" / (job.job_id + ".json"),
                grant.model_dump(mode="json"),
            )
            return grant.model_dump(mode="json")
        finally:
            AUTHORITY.reset(token)


def load_grant(settings, job_id):
    from pydantic import TypeAdapter

    from src.job_control.models import Identifier

    TypeAdapter(Identifier).validate_python(job_id)
    grant = Grant.model_validate_json(
        read_file(private(settings.root / "native-grants" / (job_id + ".json")))
    )
    if (
        grant.protocol != PROTOCOL
        or grant.job_id != job_id
        or grant.approved_uid != os.getuid()
        or not grant.approved_at <= int(time.time()) < grant.expires_at
        or not 1 <= grant.expires_at - grant.approved_at <= 600
        or grant.binding != binding(settings, grant.preview)
    ):
        raise PermissionError("Missing, invalid, changed or expired native grant")
    return grant


def worker_guard(settings):
    enrolled(settings)
    grant = WORKER.get()
    if grant is None or load_grant(settings, grant.job_id) != grant:
        raise PermissionError("One-shot native worker authority required")


def job_guard(settings, job):
    grant = WORKER.get()
    if (
        grant is None
        or job.job_id != grant.job_id
        or job.initiated_by != actor(settings).subject
        or job.process_id != grant.preview.process_id
        or job.parameters != grant.preview.parameters
        or job.input_refs != grant.preview.input_refs
    ):
        raise PermissionError("Job differs from the single authorized native job")


@contextmanager
def dispatch(settings):
    with lock(settings.root):
        worker_guard(settings)
        yield True


def child_guard(root, job_id, parent):
    """A native guardian needs the consumed grant and a live executor owner."""
    import json

    root = Path(root)
    if not safe_path(root, MARKER).exists():
        return
    record = Enrollment.model_validate_json(read_file(private(root / MARKER)))
    settings = record.settings
    grant = load_grant(settings, job_id)
    claim = json.loads(
        read_file(private(root / "native-grants" / (job_id + ".used.json")))
    )
    if (
        claim
        != dict(
            grant_sha256=fingerprint(grant.model_dump(mode="json")), worker_pid=parent
        )
        or os.getppid() != parent
    ):
        raise PermissionError("Native guardian lacks live consumed worker authority")
    fd = os.open(safe_path(root, "worker.lock"), os.O_RDWR | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        raise PermissionError("Native guardian requires active C16 executor lock")
    finally:
        os.close(fd)
