import json
from pathlib import Path

import pytest
from test_cs50_knowledge_input import context as context

from scripts.cs50_transcript_index_demo import demonstrate
from src.tools_rag.cs50_ingestion import IngestionPlan
from tests.qdrant_support import qdrant_client as qdrant_client


@pytest.mark.parametrize(
    "scope,expected", [("lecture", 1), ("python", 10), ("six", 50)]
)
def test_full_offline_source_to_persisted_qdrant_and_resume(
    context, tmp_path, scope, expected
):
    _, _, _, adapter = context
    args = (
        {"course": "cs50_python", "section": "0"}
        if scope == "lecture"
        else {"course": "cs50_python"}
        if scope == "python"
        else {"all_six": True}
    )
    directory = tmp_path / "demo"
    report = demonstrate(
        adapter, directory, **args, simulate_interruption=scope != "lecture"
    )
    assert (
        report["sources"] == expected
        and report["completed_source_tasks"] == 2 * expected
    )
    assert report["unique_source_task_ids"] == 2 * expected
    assert report["fake_http_requests"] == expected
    assert report["units"] == report["unique_points"] == 2 * expected
    assert (
        report["complete"]
        and report["resume_equal"]
        and report["hits_original_checked"]
    )
    assert (
        report["empty_cues_excluded"]
        and report["recall_at_k"] is None
        and report["mrr"] is None
    )
    if scope != "lecture":
        assert report["initial_partial_points"] == 4
    plan = IngestionPlan.model_validate_json(
        (directory / "ingestion-plan.v1.json").read_bytes()
    )
    assert IngestionPlan.model_validate_json(plan.model_dump_json()) == plan
    assert all(not Path(s.input["raw_srt_path"]).is_absolute() for s in plan.sources)
    if scope == "six":
        assert {s.input["course_id"] for s in plan.sources} == {
            "cs50x",
            "cs50_python",
            "cs50_sql",
            "cs50_ai",
            "cs50_web",
            "cs50_cybersecurity",
        }
        assert any(s.input["section_key"] == "ai" for s in plan.sources)
        cyber = next(
            s
            for s in plan.sources
            if s.input["course_id"] == "cs50_cybersecurity"
            and s.input["section_key"] == "0"
        )
        assert cyber.input["media_id"] is None
    assert json.loads((directory / "demo-report.v1.json").read_text()) == report
