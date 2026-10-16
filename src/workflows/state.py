"""Existing private C16 workspace, atomic JSON metadata, no database or queue."""

import fcntl
import os
from contextlib import contextmanager

from pydantic import TypeAdapter

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import Identifier, fingerprint
from src.tools_lecture.execute_cs50 import write_state
from src.tools_materials.storage import save_model
from src.workflows.models import State


def directory(root, workflow_id):
    TypeAdapter(Identifier).validate_python(workflow_id)
    return safe_path(root, "workflows/" + workflow_id)


def load(root, workflow_id, actor):
    path = safe_path(directory(root, workflow_id), "state.v1.json")
    if not path.exists():
        return None
    state = State.model_validate_json(read_file(path))
    report = state.report
    if (
        report.workflow_id != workflow_id
        or report.initiated_by != actor.subject
        or report.course_id not in actor.courses
    ):
        raise PermissionError("Workflow owner/course denied")
    if report.report_sha256 != fingerprint(
        report.model_dump(mode="json", exclude={"report_sha256"})
    ):
        raise ValueError("Workflow metadata hash mismatch")
    return state


@contextmanager
def locked(root, workflow_id):
    path = directory(root, workflow_id)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(
        safe_path(path, "workflow.lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield path
    finally:
        os.close(fd)


def save(root, state):
    path = directory(root, state.report.workflow_id)
    write_state(safe_path(path, "state.v1.json"), state.model_dump(mode="json"))


def archive(root, state):
    if not state or not state.report.run_id:
        return
    path = safe_path(
        directory(root, state.report.workflow_id),
        "history/" + state.report.run_id + ".json",
    )
    if not path.exists():
        save_model(path, state)
