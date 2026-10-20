"""B03: explicit sequential course scope, shared budget and verified next-pending."""

import fcntl
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import httpx
from pydantic import Field

from src.tools_knowledge.complete_cs50_lecture import complete_lecture
from src.tools_knowledge.cs50_checkpoint import (
    CheckpointConflict,
    CheckpointStore,
    Contract,
    atomic_json,
    fingerprint,
)
from src.tools_knowledge.run_cs50_lecture import (
    checked_output,
    ensure_contract,
    lecture_budget,
    prepare_lecture,
    run_lecture,
    validate_chunk,
    verify_budget,
)


class ScheduleRequest(Contract):
    schema_version: Literal[1] = 1
    concurrency: Literal[1] = 1
    course_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    job_ids: tuple[str, ...]
    plan_sha256: str

    @property
    def scope_id(self):
        return fingerprint(self.model_dump(mode="json"))


class LectureStatus(Contract):
    status: Literal["pending", "partial", "done", "unknown", "failed"] = "pending"
    expected_chunks: int = Field(ge=1)
    done_chunks: int = Field(default=0, ge=0)
    error_class: str | None = None
    completion: dict | None = None


class ScheduleState(Contract):
    schema_version: Literal[1] = 1
    scope_id: str
    lectures: dict[str, LectureStatus]


@dataclass
class CourseSchedule:
    request: ScheduleRequest
    jobs: list


class PreflightFailure(CheckpointConflict):
    def __init__(self, failures):
        self.failures = failures
        super().__init__("Selected source preflight failed; no provider dispatch")


def prepare_schedule(plan, inputs, *, course_ids, workspace, config, lecture_ids=None):
    course_ids = tuple(course_ids)
    known = {c.lecture_course.course_id for c in plan.courses}
    if (
        not course_ids
        or len(set(course_ids)) != len(course_ids)
        or not set(course_ids) <= known
    ):
        raise CheckpointConflict("Explicit unique known course IDs required")
    bindings = [
        b
        for c in plan.courses
        if c.lecture_course.course_id in course_ids
        for b in c.bindings
    ]
    if lecture_ids is not None:
        lecture_ids = tuple(lecture_ids)
        if (
            not lecture_ids
            or len(set(lecture_ids)) != len(lecture_ids)
            or not set(lecture_ids) <= {b.lecture_id for b in bindings}
        ):
            raise CheckpointConflict(
                "Explicit selected lecture IDs do not match course scope"
            )
        bindings = [b for b in bindings if b.lecture_id in lecture_ids]
    supplied = {i.source_id: i for i in inputs}
    if len(supplied) != len(inputs):
        raise CheckpointConflict("Duplicate input source ID")
    jobs = []
    failures = []
    for binding in bindings:
        try:
            input = supplied.get(binding.source_id)
            if input is None or input.binding != binding:
                raise CheckpointConflict("Missing/foreign explicit input binding")
            jobs.append(
                prepare_lecture(plan, input, workspace=workspace, config=config)
            )
        except (OSError, ValueError) as error:
            failures.append(
                {
                    "source_id": binding.source_id,
                    "course_id": binding.course_id,
                    "section_key": binding.section_key,
                    "error_class": type(error).__name__,
                }
            )
    if failures:
        raise PreflightFailure(failures)
    request = ScheduleRequest(
        course_ids=course_ids,
        source_ids=tuple(j.input.source_id for j in jobs),
        job_ids=tuple(j.identity.job_id for j in jobs),
        plan_sha256=fingerprint(plan.model_dump(mode="json")),
    )
    return CourseSchedule(request, jobs)


@contextmanager
def scheduler_lock(directory):
    directory = Path(directory).absolute()
    if any(p.is_symlink() for p in (directory, *directory.parents)):
        raise CheckpointConflict("Symlink scheduler path")
    directory.mkdir(parents=True, exist_ok=True)
    fd = os.open(
        directory / "scheduler.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise CheckpointConflict("Another scheduler owns this scope") from error
        yield
    finally:
        os.close(fd)


def job_directory(root, job):
    return Path(root) / "jobs" / fingerprint(job.input.source_id)


class InspectionFailure(CheckpointConflict):
    def __init__(self, done_chunks, error):
        self.done_chunks = done_chunks
        super().__init__("Chunk inspection blocked: " + type(error).__name__)


def inspect_job(job, directory, budget):
    from src.tools_knowledge.bind_cs50_transcript import load_knowledge_transcript

    load_knowledge_transcript(job.plan, job.input, workspace=job.workspace)
    with CheckpointStore(
        directory / "checkpoint", job.identity, job.chunks
    ).locked() as store:
        done = 0
        for chunk in job.chunks:
            try:
                verify_budget(budget, store, chunk.chunk_id)
                reused = store.reuse(
                    chunk.chunk_id,
                    lambda values, chunk=chunk: validate_chunk(job, chunk, values),
                )
                if reused is not None:
                    verify_budget(budget, store, chunk.chunk_id, validated=True)
                    done += 1
            except (OSError, ValueError) as error:
                raise InspectionFailure(done, error) from error
        return done


def run_schedule(
    schedule, directory, *, max_lectures=None, provider_factory=None, audit_only=False
):
    if max_lectures is not None and (type(max_lectures) is not int or max_lectures < 1):
        raise ValueError("Positive max_lectures required")
    root = checked_output(schedule.jobs[0], directory)
    with scheduler_lock(root):
        ensure_contract(
            root, "schedule.contract.v1.json", schedule.request.model_dump(mode="json")
        )
        budget = lecture_budget(schedule.jobs, root / "budget")
        expected = {j.input.source_id: len(j.chunks) for j in schedule.jobs}
        path = root / "schedule.status.v1.json"
        if path.is_symlink():
            raise CheckpointConflict("Symlink schedule status")
        if path.exists():
            try:
                previous = ScheduleState.model_validate_json(path.read_bytes())
                if (
                    previous.scope_id != schedule.request.scope_id
                    or {k: v.expected_chunks for k, v in previous.lectures.items()}
                    != expected
                ):
                    raise ValueError("scope")
            except (OSError, ValueError) as error:
                raise CheckpointConflict("Corrupt/foreign schedule status") from error
        rows = {k: LectureStatus(expected_chunks=n) for k, n in expected.items()}
        values = {}

        def persist():
            state = ScheduleState(scope_id=schedule.request.scope_id, lectures=rows)
            atomic_json(path, state.model_dump(mode="json"), replace=path.exists())
            return state

        blocked = False
        # Verify every source/checkpoint before spending on any pending lecture.
        for job in schedule.jobs:
            source = job.input.source_id
            try:
                done = inspect_job(job, job_directory(root, job), budget)
                if done == len(job.chunks):
                    marker, values[source] = complete_lecture(
                        job, job_directory(root, job), budget
                    )
                    rows[source] = LectureStatus(
                        status="done",
                        expected_chunks=len(job.chunks),
                        done_chunks=done,
                        completion=marker.model_dump(mode="json"),
                    )
                else:
                    rows[source] = LectureStatus(
                        status="partial" if done else "pending",
                        expected_chunks=len(job.chunks),
                        done_chunks=done,
                    )
            except (OSError, ValueError) as error:
                checkpoint = (
                    job_directory(root, job) / "checkpoint" / "checkpoint.v1.json"
                )
                unknown = False
                if checkpoint.exists() and not checkpoint.is_symlink():
                    from src.tools_knowledge.cs50_checkpoint import JobCheckpoint

                    try:
                        state = JobCheckpoint.model_validate_json(
                            checkpoint.read_bytes()
                        )
                        unknown = any(
                            c.status == "unknown" for c in state.chunks.values()
                        )
                    except ValueError:
                        pass
                rows[source] = LectureStatus(
                    status="unknown" if unknown else "failed",
                    expected_chunks=len(job.chunks),
                    done_chunks=getattr(error, "done_chunks", 0),
                    error_class=type(error).__name__,
                )
                blocked = True
        persist()
        started = 0
        if not blocked and not audit_only:
            for job in schedule.jobs:
                source = job.input.source_id
                if rows[source].status == "done":
                    continue
                if max_lectures is not None and started >= max_lectures:
                    break
                started += 1
                try:
                    run_lecture(
                        job,
                        job_directory(root, job),
                        budget,
                        provider_factory=provider_factory,
                    )
                    marker, values[source] = complete_lecture(
                        job, job_directory(root, job), budget
                    )
                    rows[source] = LectureStatus(
                        status="done",
                        expected_chunks=len(job.chunks),
                        done_chunks=len(job.chunks),
                        completion=marker.model_dump(mode="json"),
                    )
                except (OSError, ValueError, RuntimeError, httpx.HTTPError) as error:
                    from src.tools_knowledge.cs50_checkpoint import JobCheckpoint

                    state = JobCheckpoint.model_validate_json(
                        (
                            job_directory(root, job)
                            / "checkpoint"
                            / "checkpoint.v1.json"
                        ).read_bytes()
                    )
                    rows[source] = LectureStatus(
                        status="unknown"
                        if any(c.status == "unknown" for c in state.chunks.values())
                        else "failed",
                        expected_chunks=len(job.chunks),
                        done_chunks=sum(
                            c.status == "done" for c in state.chunks.values()
                        ),
                        error_class=type(error).__name__,
                    )
                    blocked = True
                persist()
                if blocked:
                    break
        state = persist()
        return state, values, budget.snapshot()
