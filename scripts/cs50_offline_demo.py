"""Synthetic SRT -> real executor/import/binder -> Fake HTTP -> full six-course Knowledge."""

import argparse
import json
import os
import socket
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def demonstrate(plan, directory, *, course_ids=None):
    from src.tools_knowledge.batch_cs50 import COURSES, prepare_batch, run_batch
    from src.tools_knowledge.bind_cs50_transcript import (
        bind_cs50_knowledge_input,
        save_portable_manifest,
    )
    from src.tools_knowledge.cs50_checkpoint import atomic_json
    from src.tools_knowledge.cs50_extraction_provider import OpenAIHTTPProvider
    from src.tools_knowledge.run_cs50_lecture import LectureRunConfig
    from src.tools_knowledge.schedule_cs50 import prepare_schedule
    from src.tools_lecture.execute_cs50 import CS50Executor

    directory = Path(directory).absolute()
    if directory.exists():
        raise FileExistsError("Demo requires exclusive new scratch directory")
    if any(
        p.is_symlink() for p in (directory, *directory.parents)
    ) or directory.is_relative_to(ROOT):
        raise ValueError("Demo must be outside repository/production roots")
    directory.mkdir(parents=True)
    workspace = directory / "synthetic-sources"
    workspace.mkdir()
    course_ids = tuple(course_ids or COURSES)
    body = b"1\n00:00:00,000 --> 00:00:20,000\nTechnical synthetic input function example.\n\n2\n00:00:20,000 --> 00:00:50,000\nTechnical synthetic print function example.\n\n3\n00:00:50,000 --> 00:01:20,000\nTechnical synthetic variable example.\n"
    executor = CS50Executor(
        plan,
        workspace=workspace,
        transport=httpx.MockTransport(lambda req: httpx.Response(200, content=body)),
    )
    inputs = []
    for course in plan.courses:
        if course.lecture_course.course_id in course_ids:
            for binding in course.bindings:
                executor.run(binding)
                inputs.append(
                    bind_cs50_knowledge_input(plan, binding, workspace=workspace)
                )
    manifest = directory / "inputs.v2.json"
    save_portable_manifest(inputs, manifest, workspace=workspace)
    cfg = LectureRunConfig(max_requests=1000, token_budget=10000000, max_seconds=3600)
    prepare = prepare_batch if len(course_ids) == 6 else prepare_schedule
    scope = prepare(
        plan, inputs, course_ids=course_ids, workspace=workspace, config=cfg
    )
    calls = []

    def handle(request):
        calls.append(request)
        data = json.loads(json.loads(request.content)["messages"][1]["content"])
        first = data["segments"][0]
        response = {
            "analysis": {"chunk_id": data["chunk_id"], "relevant": True},
            "extraction": {
                "chunk_id": data["chunk_id"],
                "statements": [
                    {
                        "statement_id": "S1",
                        "text": first["text"],
                        "semantic_type": "statement",
                        "segment_ids": [first["seg_id"]],
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
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps(response)},
                    }
                ],
            },
        )

    def provider(**kwargs):
        kwargs["api_key"] = "offline-fake"
        return OpenAIHTTPProvider(**kwargs, transport=httpx.MockTransport(handle))

    report = run_batch(scope, directory / "knowledge", provider_factory=provider)
    count = len(calls)
    resumed = run_batch(
        scope,
        directory / "knowledge",
        provider_factory=lambda **kw: (_ for _ in ()).throw(
            AssertionError("Unexpected resumed provider")
        ),
    )
    if resumed != report or len(calls) != count or not report["complete"]:
        raise AssertionError("Offline end-to-end/resume contract failed")
    report["demo"] = {
        "origin": "synthetic",
        "fake_provider_requests": count,
        "source_tasks_executed": len(inputs) * 2,
        "resume_new_requests": 0,
        "real_api_calls": 0,
        "real_downloads": 0,
    }
    atomic_json(directory / "demo.report.json", report)
    return report, scope


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan",
        type=Path,
        default=ROOT / "docs/course_sources/cs50/cs50_lecture_plan.v1.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    def forbidden(*a, **kw):
        raise RuntimeError("Demo forbids real network")

    socket.socket.connect = forbidden
    socket.create_connection = forbidden
    socket.getaddrinfo = forbidden
    for k, v in {
        "ROOT": str(args.output),
        "DATA_DIR": str(args.output / "data"),
        "CHROMA_DIR": str(args.output / "chroma"),
        "WIKI_EN_API": "https://example.invalid",
        "HEADER_AGENT": "synthetic-demo",
        "HF_API_KEY": "unused",
        "OPENAI_API_KEY": "offline-fake",
    }.items():
        os.environ[k] = v
    from src.tools_knowledge.bind_cs50_transcript import CS50AdapterPlan

    report, _ = demonstrate(
        CS50AdapterPlan.model_validate_json(args.plan.read_bytes()), args.output
    )
    print(
        json.dumps(
            {
                "complete": report["complete"],
                "lectures": report["completed_lectures"],
                "demo": report["demo"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
