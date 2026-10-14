"""Real unequal lecture sizes, correct weighted counts and checked hash references."""

import httpx
import pytest
from test_cs50_knowledge_input import context as context
from test_cs50_lecture_runner import body, fake_factory


def test_weighted_report_and_read_only_inspection(context, tmp_path):
    from src.tools_knowledge.report_cs50_schedule import (
        aggregate_schedule,
        inspect_schedule_report,
    )
    from src.tools_knowledge.run_cs50_lecture import LectureRunConfig
    from src.tools_knowledge.schedule_cs50 import prepare_schedule, run_schedule

    module, executor, _, plan = context
    workspace = tmp_path / "sources"
    workspace.mkdir()
    bindings = next(
        c for c in plan.courses if c.lecture_course.course_id == "cs50_python"
    ).bindings[:2]
    bodies = {bindings[0].transcript_url: body(1), bindings[1].transcript_url: body(80)}
    worker = executor.CS50Executor(
        plan,
        workspace=workspace,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=bodies[str(request.url)])
        ),
    )
    inputs = []
    for b in bindings:
        worker.run(b)
        inputs.append(module.bind_cs50_knowledge_input(plan, b, workspace=workspace))
    cfg = LectureRunConfig(max_requests=100, token_budget=1000000, max_seconds=3600)
    scope = prepare_schedule(
        plan,
        inputs,
        course_ids=["cs50_python"],
        lecture_ids=[b.lecture_id for b in bindings],
        workspace=workspace,
        config=cfg,
    )
    state, values, budget = run_schedule(
        scope, tmp_path / "course", provider_factory=fake_factory([])
    )
    report = aggregate_schedule(
        scope, state, values, budget, directory=tmp_path / "course"
    )
    evidence = sum(v["quality"]["metrics"]["evidence_items"] for v in values.values())
    assert report["full_chunk_evidence_ratio"] == 1 / evidence
    assert report["full_chunk_evidence_ratio"] != 0.5
    assert report["completed_lectures"] == 2 and report["complete"]
    assert report["result_origin"] == "synthetic"
    assert report["actual_tokens_known"] == 10 * len(budget.attempts)
    assert inspect_schedule_report(scope, tmp_path / "course") == report
    values[bindings[0].source_id]["quality"]["source_id"] = "foreign"
    with pytest.raises(ValueError, match="artifact hash conflict"):
        aggregate_schedule(scope, state, values, budget, directory=tmp_path / "course")


def test_partial_prefix_count_survives_failed_resume(context, tmp_path):
    from test_cs50_schedule import schedule

    from src.tools_knowledge.report_cs50_schedule import aggregate_schedule
    from src.tools_knowledge.schedule_cs50 import prepare_schedule, run_schedule

    initial = schedule(context, tmp_path, cues=20)
    config = initial.jobs[0].config.model_copy(update={"max_requests": 1})
    scope = prepare_schedule(
        initial.jobs[0].plan,
        [j.input for j in initial.jobs],
        course_ids=["cs50_python"],
        workspace=initial.jobs[0].workspace,
        config=config,
    )
    calls = []
    first, values, budget = run_schedule(
        scope, tmp_path / "course", provider_factory=fake_factory(calls)
    )
    first_report = aggregate_schedule(
        scope, first, values, budget, directory=tmp_path / "course"
    )
    second, values, budget = run_schedule(
        scope, tmp_path / "course", provider_factory=fake_factory(calls)
    )
    second_report = aggregate_schedule(
        scope, second, values, budget, directory=tmp_path / "course"
    )
    assert first_report["processed_chunks"] == second_report["processed_chunks"] == 1
    assert len(calls) == 1 and not second_report["complete"]
