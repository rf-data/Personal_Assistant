"""B05: thin six-course scope over the same sequential scheduler and budget."""

from src.tools_knowledge.cs50_checkpoint import CheckpointConflict
from src.tools_knowledge.report_cs50_schedule import aggregate_schedule
from src.tools_knowledge.schedule_cs50 import prepare_schedule, run_schedule

COURSES = (
    "cs50x",
    "cs50_python",
    "cs50_sql",
    "cs50_ai",
    "cs50_web",
    "cs50_cybersecurity",
)


def prepare_batch(plan, inputs, *, course_ids, workspace, config):
    if len(course_ids) != 6 or set(course_ids) != set(COURSES):
        raise CheckpointConflict("Six explicit original course IDs required")
    bindings = [b for c in plan.courses for b in c.bindings]
    tasks = [t for c in plan.courses for t in c.tasks]
    if (
        len(bindings) != 50
        or len({b.source_id for b in bindings}) != 50
        or len(tasks) != 100
        or len({t.task_id for t in tasks}) != 100
    ):
        raise CheckpointConflict("Expected exactly 50 bindings / 100 unique SRT tasks")
    return prepare_schedule(
        plan, inputs, course_ids=course_ids, workspace=workspace, config=config
    )


def run_batch(
    scope, directory, *, provider_factory=None, max_lectures=None, audit_only=False
):
    state, values, budget = run_schedule(
        scope,
        directory,
        provider_factory=provider_factory,
        max_lectures=max_lectures,
        audit_only=audit_only,
    )
    report = aggregate_schedule(scope, state, values, budget, directory=directory)
    resources = {j.input.resource_id for j in scope.jobs}
    report["planned_source_tasks"] = sum(
        t.resource_id in resources for c in scope.jobs[0].plan.courses for t in c.tasks
    )
    per_course = {}
    for course in scope.request.course_ids:
        sources = {j.input.source_id for j in scope.jobs if j.input.course_id == course}
        job_ids = {
            j.identity.job_id for j in scope.jobs if j.input.source_id in sources
        }
        rows = [r for r in report["sources"] if r["source_id"] in sources]
        attempts = [a for a in budget.attempts.values() if a.job_id in job_ids]
        metrics = {
            k: sum(
                values[s]["quality"]["metrics"].get(k, 0)
                for s in sources
                if s in values
            )
            for k in (
                "statements",
                "formulas",
                "evidence_items",
                "invalid_evidence_references",
            )
        }
        per_course[course] = {
            "planned_lectures": len(rows),
            "completed_lectures": sum(r["status"] == "done" for r in rows),
            "expected_chunks": sum(r["expected_chunks"] for r in rows),
            "processed_chunks": sum(r["done_chunks"] for r in rows),
            "requests_reserved": len(attempts),
            "reserved_tokens": sum(a.reserved_tokens for a in attempts),
            "quality_metrics": metrics,
            "result_origin": report["result_origin"],
        }
    report["courses"] = per_course
    return report
