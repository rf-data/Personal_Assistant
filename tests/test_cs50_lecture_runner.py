"""Full true source path with only HTTP replaced; pilot untouched."""

import json
from pathlib import Path

import httpx
import pytest
from test_cs50_knowledge_input import context as context
from test_cs50_knowledge_input import imported


def body(cues=80):
    def timestamp(n):
        return f"{n // 3600:02}:{n // 60 % 60:02}:{n % 60:02},000"

    return "\n\n".join(
        f"{i + 1}\n{timestamp(i * 5)} --> {timestamp((i + 1) * 5)}\nPython function input accepts an argument {i}."
        for i in range(cues)
    ).encode()


def planned(context, tmp_path, *, course="cs50_python", config=None, cues=80):
    module, _, _, plan = context
    workspace = tmp_path / "sources"
    workspace.mkdir(exist_ok=True)
    _, input = imported(context, workspace, course=course, body=body(cues))
    from src.tools_knowledge.run_cs50_lecture import LectureRunConfig, prepare_lecture

    job = prepare_lecture(
        plan,
        input,
        workspace=workspace,
        config=config or LectureRunConfig(max_requests=100, token_budget=1000000),
    )
    return job


def fake_factory(calls, *, failure=None):
    from src.tools_knowledge.cs50_extraction_provider import OpenAIHTTPProvider

    def handle(request):
        calls.append(request)
        if failure:
            return httpx.Response(failure)
        content = json.loads(json.loads(request.content)["messages"][1]["content"])
        raw = {
            "analysis": {"chunk_id": content["chunk_id"], "relevant": True},
            "extraction": {
                "chunk_id": content["chunk_id"],
                "statements": [
                    {
                        "statement_id": "S1",
                        "text": content["segments"][0]["text"],
                        "semantic_type": "statement",
                        "segment_ids": [content["segments"][0]["seg_id"]],
                    }
                ],
                "formulas": [],
            },
        }
        return httpx.Response(
            200,
            json={
                "usage": {"total_tokens": 10},
                "choices": [
                    {"finish_reason": "stop", "message": {"content": json.dumps(raw)}}
                ],
            },
        )

    def factory(**kw):
        kw["api_key"] = kw.get("api_key") or "offline-fake"
        return OpenAIHTTPProvider(**kw, transport=httpx.MockTransport(handle))

    return factory


def test_full_lecture_resume_and_window(context, tmp_path):
    from src.tools_knowledge.run_cs50_lecture import lecture_budget, run_lecture

    job = planned(context, tmp_path)
    assert len(job.chunks) > 2
    budget = lecture_budget([job], tmp_path / "budget")
    calls = []
    factory = fake_factory(calls)
    partial = run_lecture(
        job, tmp_path / "job", budget, indices=[0, 1], provider_factory=factory
    )
    assert partial["status"] == "active" and partial["done_chunks"] == 2
    done = run_lecture(job, tmp_path / "job", budget, provider_factory=factory)
    assert done["done_chunks"] == len(job.chunks) and len(calls) == len(job.chunks)
    run_lecture(
        job,
        tmp_path / "job",
        budget,
        provider_factory=lambda **kw: pytest.fail("reinitialized provider"),
    )
    assert len(budget.snapshot().attempts) == len(job.chunks)


@pytest.mark.parametrize("failure", [429, 500])
def test_unknown_blocks_resume(context, tmp_path, failure):
    from src.tools_knowledge.run_cs50_lecture import lecture_budget, run_lecture

    job = planned(context, tmp_path)
    budget = lecture_budget([job], tmp_path / "budget")
    calls = []
    with pytest.raises(ValueError):
        run_lecture(
            job,
            tmp_path / "job",
            budget,
            provider_factory=fake_factory(calls, failure=failure),
        )
    with pytest.raises(ValueError, match="automatic retry forbidden"):
        run_lecture(job, tmp_path / "job", budget, provider_factory=fake_factory(calls))
    assert len(calls) == 1


def test_portable_identity_and_paths(context, tmp_path):
    import shutil

    from src.tools_knowledge.bind_cs50_transcript import portable_input
    from src.tools_knowledge.run_cs50_lecture import (
        lecture_budget,
        prepare_lecture,
        run_lecture,
    )

    job = planned(context, tmp_path)
    portable = portable_input(job.input, workspace=job.workspace)
    moved = tmp_path / "moved"
    shutil.copytree(job.workspace, moved)
    relocated = prepare_lecture(job.plan, portable, workspace=moved, config=job.config)
    assert relocated.identity == job.identity
    budget = lecture_budget([job], tmp_path / "budget")
    with pytest.raises(ValueError, match="source roots"):
        run_lecture(job, job.input.raw_srt_path.parent / "knowledge", budget)
    for indices in ([0, 0], [-1], [len(job.chunks)]):
        with pytest.raises(ValueError, match="window"):
            run_lecture(job, tmp_path / "job", budget, indices=indices)


def test_offline_cli_all_chunks_and_resume(context, tmp_path):
    from scripts.cs50_lecture import main
    from src.tools_knowledge.bind_cs50_transcript import save_portable_manifest

    job = planned(context, tmp_path)
    manifest = tmp_path / "manifest.json"
    save_portable_manifest((job.input,), manifest, workspace=job.workspace)
    plan = (
        Path(__file__).resolve().parents[1]
        / "docs/course_sources/cs50/cs50_lecture_plan.v1.json"
    )
    args = [
        "--plan",
        str(plan),
        "--manifest",
        str(manifest),
        "--workspace",
        str(job.workspace),
        "--output",
        str(tmp_path / "run"),
        "--course",
        "cs50_python",
        "--section",
        "0",
        "--all-chunks",
    ]
    assert main(args) == 0
    assert main(args) == 0
    reports = [
        json.loads(p.read_text())
        for p in (tmp_path / "run" / "runs").glob("*/worker.json")
    ]
    assert all(r["status"] == "done" and r["validated"] for r in reports)
    assert all(not r["budget"]["attempts"] for r in reports)


def test_persistent_runtime_and_budget_loss(context, tmp_path):
    from src.tools_knowledge.run_cs50_lecture import lecture_budget, run_lecture

    job = planned(context, tmp_path, cues=10)
    budget = lecture_budget([job], tmp_path / "budget")
    calls = []
    run_lecture(
        job, tmp_path / "job", budget, indices=[0], provider_factory=fake_factory(calls)
    )
    runtime = budget.directory / "runtime.v1.json"
    runtime.unlink()
    with pytest.raises(ValueError, match="Runtime receipt missing"):
        run_lecture(job, tmp_path / "job", budget, provider_factory=fake_factory(calls))
    assert len(calls) == 1


def test_request_cap_blocks_fresh_process_budget(context, tmp_path):
    from src.tools_knowledge.run_cs50_lecture import (
        LectureRunConfig,
        lecture_budget,
        run_lecture,
    )

    job = planned(
        context, tmp_path, config=LectureRunConfig(max_requests=1, token_budget=60000)
    )
    budget = lecture_budget([job], tmp_path / "budget")
    calls = []
    with pytest.raises(ValueError, match="budget exhausted"):
        run_lecture(job, tmp_path / "job", budget, provider_factory=fake_factory(calls))
    assert len(calls) == 1 and len(budget.snapshot().attempts) == 1


def test_execute_gate(context, tmp_path, monkeypatch):
    from src.tools_knowledge.run_cs50_lecture import (
        LectureRunConfig,
        lecture_budget,
        run_lecture,
    )

    monkeypatch.delenv("CS50_LECTURE_EXECUTE_LLM", raising=False)
    job = planned(context, tmp_path, config=LectureRunConfig(execute_llm=True))
    budget = lecture_budget([job], tmp_path / "budget")
    with pytest.raises(ValueError, match="parent authorization"):
        run_lecture(job, tmp_path / "job", budget)
    assert not (tmp_path / "job").exists()
