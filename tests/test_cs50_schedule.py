"""Ten lectures, shared budgets, next-pending, conservative preflight and resume."""

import httpx
import pytest
from test_cs50_knowledge_input import context as context
from test_cs50_lecture_runner import body, fake_factory


def schedule(context, tmp_path, course="cs50_python", cues=10):
    from src.tools_knowledge.run_cs50_lecture import LectureRunConfig
    from src.tools_knowledge.schedule_cs50 import prepare_schedule

    module, executor, _, plan = context
    workspace = tmp_path / "sources"
    workspace.mkdir()
    worker = executor.CS50Executor(
        plan,
        workspace=workspace,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=body(cues))
        ),
    )
    inputs = []
    for course_plan in plan.courses:
        if course_plan.lecture_course.course_id == course:
            for binding in course_plan.bindings:
                worker.run(binding)
                inputs.append(
                    module.bind_cs50_knowledge_input(plan, binding, workspace=workspace)
                )
    cfg = LectureRunConfig(max_requests=1000, token_budget=10000000, max_seconds=3600)
    return prepare_schedule(
        plan, inputs, course_ids=(course,), workspace=workspace, config=cfg
    )


def test_ten_lectures_next_pending_resume(context, tmp_path):
    from src.tools_knowledge.schedule_cs50 import run_schedule

    scope = schedule(context, tmp_path)
    assert len(scope.jobs) == 10
    calls = []
    first, _, _ = run_schedule(
        scope, tmp_path / "course", max_lectures=1, provider_factory=fake_factory(calls)
    )
    assert sum(r.status == "done" for r in first.lectures.values()) == 1
    second, values, budget = run_schedule(
        scope, tmp_path / "course", provider_factory=fake_factory(calls)
    )
    assert all(r.status == "done" for r in second.lectures.values())
    assert len(values) == 10 and len(calls) == sum(len(j.chunks) for j in scope.jobs)
    third, _, _ = run_schedule(
        scope,
        tmp_path / "course",
        provider_factory=lambda **kw: pytest.fail("duplicate provider"),
    )
    assert second == third and len(budget.attempts) == len(calls)
    assert (
        type(scope.request).model_validate_json(scope.request.model_dump_json())
        == scope.request
    )


def test_invalid_source_preflight_no_dispatch(context, tmp_path):
    from src.tools_knowledge.schedule_cs50 import run_schedule

    scope = schedule(context, tmp_path)
    scope.jobs[-1].input.raw_srt_path.write_text("corrupt")
    state, _, _ = run_schedule(
        scope,
        tmp_path / "course",
        provider_factory=lambda **kw: pytest.fail("source preflight bypass"),
    )
    assert state.lectures[scope.jobs[-1].input.source_id].status == "failed"
    assert all(row.done_chunks == 0 for row in state.lectures.values())


def test_unknown_blocks_course(context, tmp_path):
    from src.tools_knowledge.schedule_cs50 import run_schedule

    scope = schedule(context, tmp_path)
    calls = []
    first, _, budget = run_schedule(
        scope, tmp_path / "course", provider_factory=fake_factory(calls, failure=500)
    )
    assert any(r.status == "unknown" for r in first.lectures.values())
    second, _, _ = run_schedule(
        scope, tmp_path / "course", provider_factory=fake_factory(calls)
    )
    assert len(calls) == 1 and len(budget.attempts) == 1
    assert any(r.status == "unknown" for r in second.lectures.values())


def test_scheduler_lock_and_corrupt_status(context, tmp_path):
    from src.tools_knowledge.schedule_cs50 import run_schedule, scheduler_lock

    scope = schedule(context, tmp_path)
    with scheduler_lock(tmp_path / "course"):
        with pytest.raises(ValueError, match="Another scheduler"):
            run_schedule(scope, tmp_path / "course")
    run_schedule(scope, tmp_path / "course", max_lectures=1)
    status = tmp_path / "course" / "schedule.status.v1.json"
    status.write_text("{broken")
    with pytest.raises(ValueError, match="schedule status"):
        run_schedule(scope, tmp_path / "course")
    assert status.read_text() == "{broken"


def test_timeout_persists_unknown(context, tmp_path):
    from src.tools_knowledge.cs50_extraction_provider import OpenAIHTTPProvider
    from src.tools_knowledge.schedule_cs50 import run_schedule

    scope = schedule(context, tmp_path)
    calls = []

    def timeout(request):
        calls.append(request)
        raise httpx.ReadTimeout("synthetic")

    def factory(**kw):
        kw["api_key"] = "offline-fake"
        return OpenAIHTTPProvider(**kw, transport=httpx.MockTransport(timeout))

    state, _, budget = run_schedule(
        scope, tmp_path / "course", provider_factory=factory
    )
    assert any(r.status == "unknown" for r in state.lectures.values())
    assert len(calls) == 1 and len(budget.attempts) == 1
