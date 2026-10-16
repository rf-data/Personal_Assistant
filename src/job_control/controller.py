"""Authorized short operations only. Actual execution belongs to the worker."""

import hashlib
import hmac
import re
import uuid

from src.job_control.catalog import prepare_indexes, resolve_preview
from src.job_control.models import Job, PreviewRequest, StartRequest, fingerprint
from src.job_control.registry import registry_document
from src.job_control.store import Conflict, Store, Unavailable, now


class AuthenticationError(PermissionError):
    pass


def authenticate(settings, authorization):
    if not isinstance(authorization, str) or not re.fullmatch(
        r"Bearer [A-Za-z0-9_-]{32,256}", authorization
    ):
        raise AuthenticationError("Authentication required")
    digest = hashlib.sha256(authorization[7:].encode()).hexdigest()
    actor = None
    for identity in settings.identities:
        if hmac.compare_digest(digest, identity.token_sha256):
            actor = identity
    if actor is None:
        raise AuthenticationError("Authentication required")
    return actor


class Controller:
    def __init__(self, settings):
        self.settings = settings
        self.store = Store(settings.root)
        self.indexes = prepare_indexes(settings)

    def authenticate(self, authorization):
        return authenticate(self.settings, authorization)

    @staticmethod
    def operator(actor):
        if actor.role != "operator":
            raise PermissionError("Operator role required")

    @staticmethod
    def allowed(actor, job):
        if job.parameters["course_id"] not in actor.courses:
            raise PermissionError("Job course scope denied")

    def preview(self, actor, value):
        request = PreviewRequest.model_validate(value)
        return resolve_preview(self.settings, request, actor, self.indexes)[0]

    def get(self, actor, job_id):
        job = self.store.get(job_id)
        self.allowed(actor, job)
        return job

    def create(self, actor, value, key):
        self.operator(actor)
        request = StartRequest.model_validate(value)
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", key):
            raise ValueError("Idempotency-Key required")
        intent = fingerprint(request.model_dump(mode="json"))

        def existing(db):
            row = db.execute(
                "SELECT id,intent FROM jobs WHERE owner=? AND request_key=?",
                (actor.subject, key),
            ).fetchone()
            if row:
                if row[1] != intent:
                    raise Conflict("Idempotency-Key payload conflict")
                job = self.store.get_db(db, row[0])
                self.allowed(actor, job)
                return job
            return None

        with self.store.connection() as db:
            old = existing(db)
            if old:
                return old
        if not self.settings.execution_enabled:
            raise Unavailable("Job creation is disabled")
        checked, entry = resolve_preview(
            self.settings,
            PreviewRequest(
                process_id=request.preview.process_id,
                parameters=request.preview.parameters,
            ),
            actor,
            self.indexes,
        )
        if checked != request.preview:
            raise Conflict("Preview changed or no longer valid")
        if request.start and not self.store.worker_available(self.settings.worker_ttl):
            raise Unavailable("Worker unavailable")
        with self.store.connection(write=True) as db:
            old = existing(db)
            if old:
                return old
            rows = [
                Job.model_validate_json(row[0])
                for row in db.execute("SELECT data FROM jobs")
            ]
            if (
                len(rows) >= self.settings.max_jobs
                or sum(
                    j.status in {"created", "queued", "cancel_requested"} for j in rows
                )
                >= self.settings.max_queued
            ):
                raise Unavailable("Job capacity reached")
            job = Job(
                job_id="job_" + uuid.uuid4().hex,
                process_id=checked.process_id,
                status="queued" if request.start else "created",
                phase="queued" if request.start else "created",
                created_at=now(),
                parameters=checked.parameters,
                initiated_by=actor.subject,
                input_refs=checked.input_refs,
                cancellable=request.start,
            )
            db.execute(
                "INSERT INTO jobs VALUES(?,?,?,?,?,?)",
                (
                    job.job_id,
                    actor.subject,
                    key,
                    intent,
                    job.model_dump_json(),
                    entry.model_dump_json(),
                ),
            )
            self.store.put_db(db, job, "Confirmed offline request accepted")
            return job

    def start(self, actor, job_id):
        self.operator(actor)
        job = self.get(actor, job_id)
        if job.initiated_by != actor.subject:
            raise PermissionError("Only the owner may start this job")
        if job.status != "created":
            return job
        if not self.settings.execution_enabled or not self.store.worker_available(
            self.settings.worker_ttl
        ):
            raise Unavailable("Execution disabled or worker unavailable")
        # Revalidate current approved bytes; executor verifies stored hashes again.
        _, entry = resolve_preview(
            self.settings,
            PreviewRequest(process_id=job.process_id, parameters=job.parameters),
            actor,
            self.indexes,
        )
        if entry != self.store.entry(job_id):
            raise Conflict("Approved input contract changed")
        return self.store.transition(job_id, "queued", "queued", "Offline job released")

    def cancel(self, actor, job_id):
        self.operator(actor)
        job = self.get(actor, job_id)
        if job.initiated_by != actor.subject:
            raise PermissionError("Only the owner may cancel this job")
        if job.status == "cancel_requested":
            return job
        if not job.cancellable:
            raise Conflict("Job is not cancellable")
        return self.store.transition(
            job_id,
            "cancel_requested",
            "cancel_requested",
            "Cancellation requested; process end not yet confirmed",
        )

    def history(
        self,
        actor,
        *,
        limit=100,
        offset=0,
        process_id=None,
        status=None,
        course_id=None,
    ):
        if not 1 <= limit <= 100 or not 0 <= offset <= 1000:
            raise ValueError("History bounds")
        jobs = [
            j
            for j in self.store.all()
            if j.parameters["course_id"] in actor.courses
            and (not process_id or j.process_id == process_id)
            and (not status or j.status == status)
            and (not course_id or j.parameters["course_id"] == course_id)
        ]
        return jobs[offset : offset + limit]

    def processes(self, actor):
        return {
            **registry_document(
                workflows=self.settings.workflows_enabled, pdf=self.settings.pdf_enabled
            ),
            "worker_available": self.store.worker_available(self.settings.worker_ttl),
            "execution_enabled": self.settings.execution_enabled,
            "courses": list(actor.courses),
            "inputs": [
                dict(
                    input_ref=ref,
                    kind=entry.kind,
                    course_ids=[c for c in entry.course_ids if c in actor.courses],
                )
                for ref, entry in self.settings.catalog.items()
                if set(entry.course_ids) & set(actor.courses)
            ],
        }
