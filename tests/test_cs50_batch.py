"""Every planned source/action/lecture through actual offline core functions."""

import pytest
from test_cs50_knowledge_input import context as context


def test_full_six_course_end_to_end_and_resume(context, tmp_path):
    from scripts.cs50_offline_demo import demonstrate

    _, _, _, plan = context
    report, scope = demonstrate(plan, tmp_path / "demo")
    assert report["completed_lectures"] == 50 and report["planned_source_tasks"] == 100
    assert len(scope.jobs) == 50 and report["demo"]["source_tasks_executed"] == 100
    assert report["expected_chunks"] == report["processed_chunks"]
    assert report["requests_reserved"] == report["demo"]["fake_provider_requests"]
    assert (
        report["demo"]["resume_new_requests"] == report["demo"]["real_api_calls"] == 0
    )
    assert (
        next(
            r
            for r in report["sources"]
            if r["course_id"] == "cs50_cybersecurity" and r["section_key"] == "0"
        )["media_id"]
        is None
    )
    assert any(
        r["course_id"] == "cs50x" and r["section_key"] == "ai"
        for r in report["sources"]
    )
    assert len({j.identity.job_id for j in scope.jobs}) == 50
    assert all(j.input.lecture_id != j.input.resource_id for j in scope.jobs)
    assert sum(c["completed_lectures"] for c in report["courses"].values()) == 50


def test_explicit_six_ids_and_cli_gate(context, tmp_path, monkeypatch):
    from src.tools_knowledge.batch_cs50 import prepare_batch
    from src.tools_knowledge.run_cs50_lecture import LectureRunConfig

    _, _, _, plan = context
    with pytest.raises(ValueError, match="Six explicit"):
        prepare_batch(
            plan,
            [],
            course_ids=["cs50_python"],
            workspace=tmp_path,
            config=LectureRunConfig(),
        )
    from scripts.cs50_schedule import main

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        main(
            [
                "--plan",
                "unused",
                "--manifest",
                "unused",
                "--workspace",
                str(tmp_path / "sources"),
                "--output",
                str(tmp_path / "output"),
                "--course",
                "cs50_python",
                "--execute-llm",
            ]
        )
    assert not (tmp_path / "output").exists()
