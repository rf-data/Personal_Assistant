"""Authorized C18 HTTP handoff; C16 alone queues, executes and cancels jobs."""

import fcntl
import hashlib
import os
import re
import time
from contextlib import contextmanager

from src.job_control.catalog import read_file, safe_path, verified_files
from src.job_control.models import TERMINAL, StartRequest, fingerprint
from src.job_control.store import Conflict, Unavailable
from src.tools_materials.storage import save_model
from src.workflows import service
from src.workflows.engine import sealed
from src.workflows.http_models import (
    WorkflowCapabilities,
    WorkflowExecuteRequest,
    WorkflowInspection,
    WorkflowInspectRequest,
    WorkflowRequestReceipt,
    WorkflowResumeRequest,
    WorkflowReuseAcceptance,
    WorkflowRunReport,
    WorkflowSubmission,
)
from src.workflows.models import VALID, State, Workflow
from src.workflows.state import load


@contextmanager
def request_lock(root):
    """Serialize only short HTTP confirmations, separately from the engine lock."""
    fd = os.open(
        safe_path(root, "workflow-http.lock"),
        os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
        0o600,
    )
    try:
        until = time.monotonic() + 5
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= until:
                    raise Unavailable("Workflow confirmation busy") from None
                time.sleep(0.01)
        yield
    finally:
        os.close(fd)


class WorkflowHTTP:
    def __init__(self, controller):
        self.controller = controller
        self.settings = controller.settings

    def capabilities(self):
        return WorkflowCapabilities(
            enabled=self.settings.workflows_enabled,
            execution_enabled=self.settings.execution_enabled,
            worker_available=self.controller.store.worker_available(
                self.settings.worker_ttl
            ),
        )

    def authorize(self, actor, source_ref):
        if not self.settings.workflows_enabled:
            raise PermissionError("Workflow API disabled")
        entry = self.settings.catalog.get(source_ref)
        if entry is None or entry.kind != "workflow_bundle":
            raise ValueError("Approved workflow bundle required")
        if not set(entry.course_ids) & set(actor.courses):
            raise PermissionError("Course denied")

    def job_scope(self, actor, job, request):
        if (
            job.initiated_by != actor.subject
            or job.parameters["course_id"] not in actor.courses
            or job.parameters["course_id"]
            not in self.settings.catalog[request.source_ref].course_ids
        ):
            raise PermissionError("Workflow owner/course denied")
        if (
            job.process_id != "cs50_offline_workflow"
            or job.parameters["workflow_id"] != request.workflow_id
            or job.input_refs != (request.source_ref,)
        ):
            raise Conflict("Workflow source/run identity conflict")

    def report_scope(self, actor, report, request, history):
        """Reject forged references before C18 reads any referenced stage bytes."""
        if (
            report != sealed(report)
            or report.workflow_id != request.workflow_id
            or report.input_refs != (request.source_ref,)
            or report.initiated_by != actor.subject
            or report.course_id not in actor.courses
            or report.run_id not in history
        ):
            raise ValueError("Invalid persisted workflow report identity/hash")
        lineage = set()
        run_id = report.run_id
        while run_id is not None:
            if run_id in lineage or run_id not in history:
                raise ValueError("Invalid workflow run lineage")
            lineage.add(run_id)
            job = history[run_id]
            self.job_scope(actor, job, request)
            if job.parameters["course_id"] != report.course_id:
                raise ValueError("Report course contradicts run")
            run_id = job.parameters["previous_run_id"]
        refs = set()
        for stage in report.stages:
            for output in stage.output_refs:
                prefix = (
                    f"jobs/{stage.job_id}/results/stages/"
                    + fingerprint(stage.stage_id)[:32]
                    + "/"
                )
                if stage.job_id not in lineage or not output.path.startswith(prefix):
                    raise ValueError("Stage artifact outside producing run/stage")
                refs.add(output.model_dump_json())
        if any(o.model_dump_json() not in refs for o in report.output_refs):
            raise ValueError("Unbound workflow output reference")

    def read(self, actor, value, *, offset=0, limit=10):
        request = WorkflowInspectRequest.model_validate(value)
        self.authorize(actor, request.source_ref)
        if not 0 <= offset <= 1000 or not 1 <= limit <= 100:
            raise ValueError("Workflow history bounds")
        history = tuple(
            j
            for j in service.jobs(self.settings)
            if j.process_id == "cs50_offline_workflow"
            and j.parameters["workflow_id"] == request.workflow_id
        )
        for job in history:
            self.job_scope(actor, job, request)
        indexed = {j.job_id: j for j in history}
        state = load(self.settings.root, request.workflow_id, actor)
        if state:
            self.report_scope(actor, state.report, request, indexed)
            if any(attempt not in indexed for attempt in state.attempts):
                raise ValueError("Unbound workflow attempt")
        # Only the existing C18 service computes stage decisions and reuse.
        try:
            report, prepared, current = service.inspect(
                self.settings, actor, request.source_ref, request.workflow_id
            )
        except (KeyError, StopIteration) as error:
            raise ValueError("Invalid approved workflow bundle") from error
        _stored, artifact = self.artifact_report(actor, request, current, indexed)
        return WorkflowInspection(
            preview_id=service.preview_id(
                self.settings, actor, request.source_ref, report, prepared, current
            ),
            workflow=report,
            persisted_report=state.report if state else None,
            current_job=current,
            previous_run_id=current.parameters["previous_run_id"] if current else None,
            report_artifact=artifact,
            history=history[offset : offset + limit],
            history_total=len(history),
            history_offset=offset,
            history_limit=limit,
        )

    def artifact_report(self, actor, request, job, history):
        # Reports are read exclusively from the fixed adapter output, never a URL/path.
        if job and job.artifact_refs:
            (artifact,) = job.artifact_refs
            if (
                artifact.kind != "workflow_report"
                or artifact.input_refs != job.input_refs
            ):
                raise ValueError("Invalid report artifact metadata")
            path = safe_path(
                self.settings.root,
                f"jobs/{job.job_id}/results/{job.parameters['output_name']}.json",
            )
            data = read_file(path)
            if (
                len(data) != artifact.size_bytes
                or hashlib.sha256(data).hexdigest() != artifact.sha256
            ):
                raise ValueError("Report artifact hash/size mismatch")
            stored = Workflow.model_validate_json(data)
            self.report_scope(actor, stored, request, history)
            if stored.run_id != job.job_id:
                raise ValueError("Report artifact run mismatch")
            return stored, artifact
        return None, None

    def run_report(self, actor, workflow_id, run_id, source_ref):
        request = WorkflowInspectRequest(source_ref=source_ref, workflow_id=workflow_id)
        self.authorize(actor, source_ref)
        history = {
            j.job_id: j
            for j in service.jobs(self.settings)
            if j.process_id == "cs50_offline_workflow"
            and j.parameters["workflow_id"] == workflow_id
        }
        for job in history.values():
            self.job_scope(actor, job, request)
        job = history[run_id]
        report, artifact = self.artifact_report(actor, request, job, history)
        if report is None:
            state = load(self.settings.root, workflow_id, actor)
            if state and state.report.run_id == run_id:
                report = state.report
            else:
                path = safe_path(
                    self.settings.root,
                    f"workflows/{workflow_id}/history/{job.job_id}.json",
                )
                if path.exists():
                    report = State.model_validate_json(read_file(path)).report
            if report:
                self.report_scope(actor, report, request, history)
                if report.run_id != run_id:
                    raise ValueError("Archived report run mismatch")
        return WorkflowRunReport(
            workflow_id=workflow_id,
            run_id=run_id,
            job=job,
            report=report,
            report_artifact=artifact,
        )

    def replay(self, actor, receipt, path):
        if receipt.owner != actor.subject:
            raise PermissionError("Workflow request owner denied")
        if receipt.existing_job_id:
            accepted = safe_path(path.parent, "accepted/" + path.name)
            if not accepted.exists():
                # A reservation alone is never proof of successful reuse:
                # service.submit may have rejected a concurrently stale preview.
                return None
            marker = WorkflowReuseAcceptance.model_validate_json(
                read_file(accepted, 32768)
            )
            if (
                marker.intent != receipt.intent
                or marker.job_id != receipt.existing_job_id
            ):
                raise ValueError("Invalid workflow reuse acceptance")
            job = self.controller.store.get(receipt.existing_job_id)
        else:
            key = service.request_key(
                actor, receipt.request.workflow_id, receipt.request.current_run_id
            )
            with self.controller.store.connection() as db:
                row = db.execute(
                    "SELECT id,intent FROM jobs WHERE owner=? AND request_key=?",
                    (actor.subject, key),
                ).fetchone()
            if not row:
                return None
            if row[1] != receipt.c16_intent:
                raise Conflict("Pending workflow request contract changed")
            job = self.controller.store.get(row[0])
        self.job_scope(actor, job, receipt.request)
        return job

    def submit(self, actor, value, key, *, resume=False):
        request = (
            WorkflowResumeRequest if resume else WorkflowExecuteRequest
        ).model_validate(value)
        self.controller.operator(actor)
        self.authorize(actor, request.source_ref)
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", key):
            raise ValueError("Idempotency-Key required")
        operation = "resume" if resume else "execute"
        intent = fingerprint(
            dict(operation=operation, request=request.model_dump(mode="json"))
        )
        name = fingerprint(dict(owner=actor.subject, key=key))
        with request_lock(self.settings.root):
            path = safe_path(self.settings.root, "workflow-requests/" + name + ".json")
            if path.exists():
                receipt = WorkflowRequestReceipt.model_validate_json(
                    read_file(path, 32768)
                )
                if (
                    receipt.intent != intent
                    or fingerprint(
                        dict(
                            operation=receipt.operation,
                            request=receipt.request.model_dump(mode="json"),
                        )
                    )
                    != intent
                ):
                    raise Conflict("Idempotency-Key payload conflict")
                job = self.replay(actor, receipt, path)
                if job:
                    return self.submission(request, job)
            checked = self.read(
                actor,
                WorkflowInspectRequest(
                    source_ref=request.source_ref, workflow_id=request.workflow_id
                ),
            )
            current = checked.current_job
            if (
                checked.preview_id != request.preview_id
                or (current.job_id if current else None) != request.current_run_id
            ):
                raise Conflict("Workflow preview/run changed")
            # Even a no-new-job reuse requires all currently approved input bytes.
            try:
                verified_files(self.settings.catalog[request.source_ref])
            except KeyError as error:
                raise ValueError("Invalid approved workflow manifest") from error
            reusable = current and (
                current.status not in TERMINAL
                or not resume
                or (
                    checked.workflow.status == "completed"
                    and all(s.status in VALID for s in checked.workflow.stages)
                )
            )
            if not path.exists():
                directory = path.parent
                directory.mkdir(mode=0o700, exist_ok=True)
                if (
                    sum(1 for _ in directory.glob("*.json"))
                    >= self.settings.max_jobs * 10
                ):
                    raise Unavailable("Workflow request receipt capacity reached")
                c16_intent = None
                if not reusable:
                    preview = self.controller.preview(
                        actor,
                        dict(
                            process_id="cs50_offline_workflow",
                            parameters=dict(
                                source_ref=request.source_ref,
                                course_id=checked.workflow.course_id,
                                workflow_id=request.workflow_id,
                                previous_run_id=request.current_run_id,
                            ),
                        ),
                    )
                    c16_intent = fingerprint(
                        StartRequest(preview=preview, confirmed=True).model_dump(
                            mode="json"
                        )
                    )
                # Reserve the exact intent before delegation. A crash after C16's
                # transaction is recovered by its existing stable workflow key.
                save_model(
                    path,
                    WorkflowRequestReceipt(
                        owner=actor.subject,
                        intent=intent,
                        request=request,
                        operation=operation,
                        existing_job_id=current.job_id if reusable else None,
                        c16_intent=c16_intent,
                    ),
                )
            job = service.submit(
                self.settings,
                actor,
                request.source_ref,
                request.workflow_id,
                resume=resume,
                expected_preview_id=request.preview_id,
                expected_run_id=request.current_run_id,
            )
            if reusable:
                accepted = safe_path(path.parent, "accepted/" + path.name)
                accepted.parent.mkdir(mode=0o700, exist_ok=True)
                save_model(
                    accepted, WorkflowReuseAcceptance(intent=intent, job_id=job.job_id)
                )
            return self.submission(request, job)

    @staticmethod
    def submission(request, job):
        return WorkflowSubmission(
            workflow_id=request.workflow_id,
            run_id=job.job_id,
            job=job,
        )
