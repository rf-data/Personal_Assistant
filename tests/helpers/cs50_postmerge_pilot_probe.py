"""Synthetic temporary receipts; run existing legacy/precise tests unchanged."""

import os
import socket
import sys
import tempfile
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    sys.path[:0] = [str(root), str(root / "tests")]
    workspace = Path(tempfile.mkdtemp(prefix="cs50-audit-synthetic-"))
    os.environ.update(
        ROOT=str(workspace),
        DATA_DIR=str(workspace / "data"),
        CHROMA_DIR=str(workspace / "chroma"),
        WIKI_EN_API="https://example.invalid",
        HEADER_AGENT="offline",
        HF_API_KEY="unused",
        OPENAI_API_KEY="unused",
    )

    def forbidden(*a, **kw):
        raise AssertionError("Network forbidden")

    socket.socket.connect = forbidden
    socket.socket.connect_ex = forbidden
    socket.create_connection = forbidden
    socket.getaddrinfo = forbidden
    import httpx
    import pytest

    from src.tools_knowledge.bind_cs50_transcript import (
        CS50AdapterPlan,
        CS50KnowledgeInputManifest,
        bind_cs50_knowledge_input,
        save_knowledge_manifest,
    )
    from src.tools_lecture.execute_cs50 import CS50Executor

    plan_path = root / "docs/course_sources/cs50/cs50_lecture_plan.v1.json"
    plan = CS50AdapterPlan.model_validate_json(plan_path.read_bytes())

    def timestamp(second):
        return f"{second // 3600:02}:{second // 60 % 60:02}:{second % 60:02},000"

    body = "\n\n".join(
        f"{i + 1}\n{timestamp(i * 5)} --> {timestamp((i + 1) * 5)}\n"
        + (
            [
                "A variable stores a value in Python.",
                "The print function displays text.",
            ][i % 2]
        )
        for i in range(400)
    ).encode()
    worker = CS50Executor(
        plan,
        workspace=workspace,
        transport=httpx.MockTransport(lambda req: httpx.Response(200, content=body)),
    )
    binding = worker.select(course="cs50_python", section="0")[0]
    worker.run(binding)
    entry = bind_cs50_knowledge_input(plan, binding, workspace=workspace)
    manifest = workspace / "synthetic-input.json"
    save_knowledge_manifest(CS50KnowledgeInputManifest(inputs=(entry,)), manifest)

    class Context:
        def pytest_collection_modifyitems(self, items):
            for item in items:
                item.module.ROOT = workspace
                item.module.PLAN = plan_path
                item.module.MANIFEST = manifest

    sys.exit(
        pytest.main(
            [
                "tests/test_cs50_knowledge_pilot.py::test_fake_llm_full_pilot_binding",
                "tests/test_cs50_knowledge_pilot.py::test_fake_worker_two_chunks",
                "tests/test_cs50_precise_evidence.py::test_full_pilot_preserves_source_and_consolidates",
                "tests/test_cs50_precise_evidence.py::test_invalid_provider_saved_no_precise_output",
                "tests/test_cs50_quality.py::test_capture_before_overwrite_on_real_concept_fixture",
                f"--junitxml={workspace / 'pilot-tests.xml'}",
                "-q",
            ],
            plugins=[Context()],
        )
    )


if __name__ == "__main__":
    main()
