"""B04: weighted quality/coverage from validated completion sets, never ratios averaged."""

import hashlib
from collections import Counter

from src.tools_knowledge.complete_cs50_lecture import FILES, LectureCompletion
from src.tools_knowledge.cs50_checkpoint import CheckpointConflict, encoded
from src.tools_knowledge.schedule_cs50 import job_directory, run_schedule


def aggregate_schedule(schedule, state, values, budget, *, directory):
    if state.scope_id != schedule.request.scope_id or set(state.lectures) != set(
        schedule.request.source_ids
    ):
        raise CheckpointConflict("Foreign aggregate scope")
    jobs = {j.input.source_id: j for j in schedule.jobs}
    done = {k for k, r in state.lectures.items() if r.status == "done"}
    if set(values) != done:
        raise CheckpointConflict(
            "Aggregate requires exactly all validated completed lecture values"
        )
    metrics = Counter()
    scopes = Counter()
    sources = []
    for source, row in state.lectures.items():
        job = jobs[source]
        if (
            row.expected_chunks != len(job.chunks)
            or row.done_chunks > row.expected_chunks
        ):
            raise CheckpointConflict("Aggregate chunk denominator conflict")
        if source in done:
            marker = LectureCompletion.model_validate(row.completion)
            if (
                marker.phase != "done"
                or marker.job_id != job.identity.job_id
                or marker.expected_chunk_ids != job.identity.selected_chunks
                or set(marker.artifacts) != set(FILES)
            ):
                raise CheckpointConflict("Aggregate completion identity conflict")
            for key, value in values[source].items():
                if (
                    key not in FILES
                    or hashlib.sha256(encoded(value)).hexdigest()
                    != marker.artifacts[key]
                ):
                    raise CheckpointConflict("Aggregate artifact hash conflict")
            coverage = values[source]["coverage"]
            if (
                coverage["source_id"] != source
                or coverage["expected_chunks"] != row.expected_chunks
                or coverage["processed_chunks"] != row.expected_chunks
            ):
                raise CheckpointConflict("Aggregate source/coverage conflict")
            quality = values[source]["quality"]
            if (
                quality["source_id"] != source
                or quality["course_id"] != job.input.course_id
                or quality["lecture_id"] != job.input.lecture_id
            ):
                raise CheckpointConflict("Aggregate quality identity conflict")
            metrics.update(
                {k: v for k, v in quality["metrics"].items() if type(v) is int}
            )
            scopes.update(quality["evidence_scope_counts"])
        sources.append(
            {
                "course_id": job.input.course_id,
                "section_key": job.input.section_key,
                "lecture_id": job.input.lecture_id,
                "resource_id": job.input.resource_id,
                "source_id": source,
                "media_id": job.input.media_id,
                "transcript_url": job.input.transcript_url,
                "transcript_sha256": job.input.transcript_sha256,
                "result_reference": str(
                    job_directory(directory, job).relative_to(directory)
                    / "completion.v1.json"
                ),
                **row.model_dump(mode="json"),
            }
        )
    denominator = metrics["evidence_items"]
    attempts = budget.attempts.values()
    known = [
        a.usage["total_tokens"]
        for a in attempts
        if a.usage and type(a.usage.get("total_tokens")) is int
    ]
    return {
        "schema_version": 1,
        "scope_id": state.scope_id,
        "course_ids": list(schedule.request.course_ids),
        "result_origin": "LLM" if schedule.jobs[0].config.execute_llm else "synthetic",
        "planned_lectures": len(jobs),
        "completed_lectures": len(done),
        "lecture_statuses": dict(Counter(r.status for r in state.lectures.values())),
        "expected_chunks": sum(r.expected_chunks for r in state.lectures.values()),
        "processed_chunks": sum(r.done_chunks for r in state.lectures.values()),
        "complete": len(done) == len(jobs),
        "quality_lectures": len(done),
        "quality_metrics": dict(metrics),
        "evidence_scope_counts": dict(scopes),
        "full_chunk_evidence_ratio": metrics["full_chunk_evidence_items"] / denominator
        if denominator
        else None,
        "requests_reserved": len(budget.attempts),
        "reserved_tokens": budget.reserved_tokens,
        "actual_tokens_known": sum(known),
        "usage_unknown_attempts": len(budget.attempts) - len(known),
        "attempt_statuses": dict(Counter(a.status for a in budget.attempts.values())),
        "sources": sources,
        "limits": [
            "Quality counts cover completed lectures; partial chunk facts are not falsely treated as complete documents",
            "Schema and segment-ID validation do not establish entailment or didactic learning value",
        ],
    }


def inspect_schedule_report(schedule, directory):
    """Read/revalidate all sources and completion artifacts; never dispatch providers."""
    state, values, budget = run_schedule(schedule, directory, audit_only=True)
    return aggregate_schedule(schedule, state, values, budget, directory=directory)
