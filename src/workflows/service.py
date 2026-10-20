"""Workflow lifecycle delegates every actual run/cancel to the existing C16 queue."""

import sqlite3
from contextlib import closing
from urllib.parse import quote

from src.job_control.catalog import safe_path
from src.job_control.controller import Controller
from src.job_control.models import TERMINAL, Job, fingerprint
from src.job_control.registry import registry_document
from src.job_control.store import Conflict
from src.workflows.definition import prepare
from src.workflows.engine import preview, sealed
from src.workflows.models import VALID
from src.workflows.state import load


def jobs(settings):
    path = safe_path(settings.root, "jobs.sqlite3")
    if not path.exists():
        return ()
    with closing(
        sqlite3.connect(
            "file:" + quote(str(path), safe="/") + "?mode=ro", uri=True, timeout=2
        )
    ) as db:
        return tuple(
            Job.model_validate_json(r[0])
            for r in db.execute("SELECT data FROM jobs ORDER BY rowid DESC")
        )


def latest(settings, actor, workflow_id):
    for job in jobs(settings):
        if (
            job.process_id == "cs50_offline_workflow"
            and job.parameters["workflow_id"] == workflow_id
        ):
            if (
                job.initiated_by != actor.subject
                or job.parameters["course_id"] not in actor.courses
            ):
                raise PermissionError("Workflow owner/course denied")
            return job
    return None


def inspect(settings, actor, source_ref, workflow_id):
    entry = settings.catalog.get(source_ref)
    if entry is None or entry.kind != "workflow_bundle":
        raise ValueError("Approved workflow bundle required")
    if not set(entry.course_ids) & set(actor.courses):
        raise PermissionError("Course denied")
    prepared = prepare(entry, strict=False)
    if prepared.definition.course_id not in actor.courses:
        raise PermissionError("Course denied")
    previous = load(settings.root, workflow_id, actor)
    if previous and (
        previous.report.input_refs != (source_ref,)
        or previous.report.course_id != prepared.definition.course_id
    ):
        raise ValueError("Stable workflow identity/source scope conflict")
    report = preview(prepared, settings.root, workflow_id, source_ref, actor, previous)
    current = latest(settings, actor, workflow_id)
    if current and current.input_refs != (source_ref,):
        raise ValueError("Stable workflow source scope conflict")
    if current and current.status not in TERMINAL:
        # Read only; no reconciliation or process control in preview/status.
        active = (
            previous.report
            if previous and previous.report.run_id == current.job_id
            else report
        )
        report = sealed(
            active.model_copy(
                update=dict(
                    run_id=current.job_id,
                    status="running"
                    if current.status in {"running", "cancel_requested"}
                    else "pending",
                )
            )
        )
    elif (
        current
        and previous
        and current.job_id == previous.report.run_id
        and current.status != "completed"
    ):
        stages = tuple(
            s.model_copy(
                update=dict(
                    status="cancelled"
                    if current.status == "cancelled"
                    else "interrupted"
                    if current.status == "interrupted"
                    else "failed",
                    error="C16 execution ended: " + current.status,
                    finished_at=current.finished_at,
                )
            )
            if s.status == "running"
            else s
            for s in previous.report.stages
        )
        report = sealed(
            previous.report.model_copy(
                update=dict(
                    stages=stages,
                    status="cancelled"
                    if current.status == "cancelled"
                    else "interrupted"
                    if current.status == "interrupted"
                    else "failed",
                    finished_at=current.finished_at,
                )
            )
        )
    if current and current.status in {"failed", "interrupted", "cancelled"}:
        report = sealed(
            report.model_copy(
                update=dict(
                    run_id=current.job_id,
                    status=current.status,
                    started_at=current.started_at,
                    finished_at=current.finished_at,
                    errors=(
                        "C16:"
                        + current.status
                        + ":"
                        + str(current.exit_code)
                        + ":"
                        + str(current.error_class),
                    ),
                )
            )
        )
    return report, prepared, current


def preview_id(settings, actor, source_ref, report, prepared, current):
    """Bind confirmation to C18 decisions, approved bytes and execution policy."""
    return fingerprint(
        dict(
            protocol="personal_assistant_workflows_v1",
            subject=actor.subject,
            role=actor.role,
            courses=actor.courses,
            report=report.model_dump(mode="json"),
            current=current.model_dump(mode="json") if current else None,
            catalog=settings.catalog[source_ref].model_dump(mode="json"),
            definition=prepared.definition.model_dump(mode="json"),
            input_errors=prepared.input_errors,
            files={
                name: fingerprint_bytes(data) for name, data in prepared.files.items()
            },
            policy={
                name: getattr(settings, name)
                for name in (
                    "execution_enabled",
                    "workflows_enabled",
                    "pdf_enabled",
                    "max_jobs",
                    "max_queued",
                    "max_parallel",
                    "worker_ttl",
                )
            },
            registry=registry_document(workflows=True, pdf=True),
        )
    )


def fingerprint_bytes(data):
    import hashlib

    return hashlib.sha256(data).hexdigest()


def request_key(actor, workflow_id, previous):
    return (
        "workflow_"
        + fingerprint(
            dict(owner=actor.subject, workflow_id=workflow_id, previous=previous)
        )[:48]
    )


def submit(
    settings,
    actor,
    source_ref,
    workflow_id,
    *,
    resume=False,
    expected_preview_id=None,
    expected_run_id=None,
):
    if actor.role != "operator" or not settings.workflows_enabled:
        raise PermissionError("Explicit workflow/operator approval required")
    report, prepared, current = inspect(settings, actor, source_ref, workflow_id)
    if expected_preview_id is not None:
        if (current.job_id if current else None) != expected_run_id or preview_id(
            settings, actor, source_ref, report, prepared, current
        ) != expected_preview_id:
            raise Conflict("Workflow preview/run changed")
        if prepared.input_errors:
            raise ValueError("Approved input hashes/files are missing or invalid")
    if current and current.status not in TERMINAL:
        return current
    if current and not resume:
        return current
    if (
        current
        and report.status == "completed"
        and all(s.status in VALID for s in report.stages)
    ):
        return current
    if prepared.input_errors:
        raise ValueError("Approved input hashes/files are missing or invalid")
    previous = current.job_id if current else None
    controller = Controller(settings)
    checked = controller.preview(
        actor,
        dict(
            process_id="cs50_offline_workflow",
            parameters=dict(
                source_ref=source_ref,
                course_id=prepared.definition.course_id,
                workflow_id=workflow_id,
                previous_run_id=previous,
            ),
        ),
    )
    key = request_key(actor, workflow_id, previous)
    return controller.create(
        actor, dict(preview=checked.model_dump(mode="json"), confirmed=True), key
    )


def markdown(report):
    lines = [
        f"# Workflow {report.workflow_id}",
        "",
        f"Course: {report.course_id} · Status: {report.status}",
        f"Run/Job: {report.run_id or 'not started'}",
        f"Lectures: {', '.join(report.lecture_ids) or 'none'}",
        *("Error: " + error for error in report.errors),
        "",
        "| Stage | Process | Status | Decision | Job |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {s.stage_id} | {s.process_id} | {s.status} | {s.decision} | {s.job_id or '-'} |"
        for s in report.stages
    )
    for stage in report.stages:
        if stage.stale_reasons or stage.error:
            lines.extend(
                [
                    "",
                    stage.stage_id
                    + ": "
                    + ", ".join(
                        (*stage.stale_reasons, *((stage.error,) if stage.error else ()))
                    ),
                ]
            )
    return "\n".join(lines) + "\n"
