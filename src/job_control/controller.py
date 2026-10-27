"""Authorized short operations only. Actual execution belongs to the worker."""

import hashlib
import hmac
import re
import uuid

from src.job_control.catalog import (
    prepare_indexes,
    read_file,
    resolve_preview,
    safe_path,
)
from src.job_control.models import Job, PreviewRequest, StartRequest, fingerprint
from src.job_control.registry import registry_document
from src.job_control.store import Conflict, Quarantined, Store, Unavailable, now


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
        from src.job_control.deployment_gate import settings_digest

        if settings.deployment_gate_required:
            from src.job_control.deployment_gate import require_existing_queue

            require_existing_queue(settings)
        self.store = Store(
            settings.root,
            deployment_gate_required=settings.deployment_gate_required,
            deployment_gate_protocol=settings.deployment_gate_protocol,
            coordinator_test_required=settings.coordinator_test_required,
            gate_settings_sha256=settings_digest(settings),
        )
        self.indexes = prepare_indexes(settings)

    def authenticate(self, authorization):
        return authenticate(self.settings, authorization)

    @staticmethod
    def operator(actor):
        if actor.role != "operator":
            raise PermissionError("Operator role required")

    def allowed(self, actor, job):
        if job.process_id in {"content_index_build", "content_import"}:
            from src.content_store.errors import ContentStoreError, Forbidden, NotFound

            if job.process_id == "content_import":
                from src.job_control.import_jobs import authorize_job
            else:
                from src.job_control.index_jobs import authorize_job

            try:
                authorize_job(self.store, job, actor)
            except (Forbidden, NotFound):
                raise KeyError("Index job unavailable") from None
            except (ContentStoreError, ValueError, OSError):
                raise Unavailable("Index job unavailable") from None
        if job.parameters["course_id"] not in actor.courses:
            raise PermissionError("Job course scope denied")

    def preview(self, actor, value):
        request = PreviewRequest.model_validate(value)
        return resolve_preview(self.settings, request, actor, self.indexes)[0]

    def get(self, actor, job_id):
        job = self.store.get(job_id)
        self.allowed(actor, job)
        return job

    def planning_result(self, actor, job_id):
        """Read one completed, hash-bound plan; never accepts filesystem paths."""
        job = self.get(actor, job_id)
        if safe_path(self.settings.root, "quarantine").exists():
            raise Quarantined("Workspace requires operator review")
        if (
            job.process_id != "material_planning"
            or job.status != "completed"
            or len(job.artifact_refs) != 1
            or job.artifact_refs[0].kind != "material_plan"
        ):
            raise Conflict("Completed material plan required")
        artifact = job.artifact_refs[0]
        limit = 256 * 1024
        if artifact.size_bytes > limit:
            raise Unavailable("Planning result response limit")
        try:
            path = safe_path(
                self.store.directory(job_id),
                "results/" + job.parameters["output_name"] + ".json",
            )
            data = read_file(path, limit)
            if (
                len(data) != artifact.size_bytes
                or hashlib.sha256(data).hexdigest() != artifact.sha256
            ):
                raise ValueError("Planning result integrity")
            from src.tools_materials.processing import MaterialPlan

            plan = MaterialPlan.model_validate_json(data)
        except (ValueError, OSError):
            raise Unavailable("Planning result unavailable") from None
        if safe_path(self.settings.root, "quarantine").exists():
            raise Quarantined("Workspace requires operator review")
        return dict(
            schema_version=1,
            protocol="personal_assistant_material_plan_v1",
            artifact=artifact.model_dump(mode="json"),
            plan=plan.model_dump(mode="json"),
        )

    def create(self, actor, value, key):
        self.operator(actor)
        request = StartRequest.model_validate(value)
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", key):
            raise ValueError("Idempotency-Key required")
        if (
            request.preview.process_id == "content_import"
            and request.preview.parameters.get("request_key") != key
        ):
            raise ValueError("Import request key differs from confirmed plan")
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
        from src.job_control.deployment_gate import admission

        with admission(self.settings), self.store.connection(write=True) as db:
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

        def visible(job):
            if job.process_id not in {"content_index_build", "content_import"}:
                return True
            try:
                self.allowed(actor, job)
                return True
            except (PermissionError, KeyError, Unavailable):
                return False

        jobs = [
            j
            for j in self.store.all()
            if j.parameters["course_id"] in actor.courses
            and (not process_id or j.process_id == process_id)
            and (not status or j.status == status)
            and (not course_id or j.parameters["course_id"] == course_id)
            and visible(j)
        ]
        return jobs[offset : offset + limit]

    def processes(self, actor):
        return {
            **registry_document(
                workflows=self.settings.workflows_enabled,
                pdf=self.settings.pdf_enabled,
                index=self.settings.index_jobs_enabled,
                imports=self.settings.import_jobs_enabled,
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
                and entry.kind not in {"index_bundle", "content_import_bundle"}
            ],
        }
