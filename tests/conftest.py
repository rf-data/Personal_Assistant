"""Portable pilot artifacts built exclusively through the real offline pipeline."""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

pytest_plugins = ["tests.profile_policy"]


@pytest.fixture(autouse=True)
def preserve_process_umask(request):
    """CLI entrypoints may set umask too; restore state across every test."""
    # Read via a temporarily stricter mask, never via the permissive umask(0).
    previous = os.umask(0o077)
    os.umask(previous)
    request.addfinalizer(lambda: os.umask(previous))


@pytest.fixture
def private_umask(request, preserve_process_umask):
    """Restore even when a dependent fixture fails before reaching its yield."""
    previous = os.umask(0o077)
    request.addfinalizer(lambda: os.umask(previous))


@pytest.fixture(autouse=True)
def portable_cs50_pilot(request, tmp_path, monkeypatch):
    modules = {
        "test_cs50_knowledge_pilot",
        "test_cs50_quality",
        "test_cs50_precise_evidence",
    }
    if request.module.__name__.split(".")[-1] not in modules:
        return None
    names = {
        "test_offline_synthetic_subprocess",
        "test_fake_llm_full_pilot_binding",
        "test_fake_worker_two_chunks",
        "test_offline_index_selection",
        "test_capture_before_overwrite_on_synthetic_concept_fixture",
        "test_full_pilot_preserves_source_and_consolidates",
        "test_invalid_provider_saved_no_precise_output",
    }
    if request.function.__name__ not in names:
        return None
    # Settings and socket guards precede the real application imports.
    request.getfixturevalue("controlled_settings")
    from src.core.config_knowledge import KnowledgeSettings
    from src.tools_knowledge.bind_cs50_transcript import (
        CS50AdapterPlan,
        CS50KnowledgeInputManifest,
        bind_cs50_knowledge_input,
        build_cs50_knowledge_chunks,
        save_knowledge_manifest,
    )
    from src.tools_lecture.execute_cs50 import CS50Executor

    plan_path = (
        Path(__file__).resolve().parents[1]
        / "docs/course_sources/cs50/cs50_lecture_plan.v1.json"
    )
    plan = CS50AdapterPlan.model_validate_json(plan_path.read_bytes())
    workspace = tmp_path / "synthetic-workspace"
    workspace.mkdir()

    def timestamp(seconds):
        return f"{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02},000"

    texts = (
        "Python input function takes an argument.",
        "The print function displays a message.",
    )
    body = "\n\n".join(
        f"{i + 1}\n{timestamp(i * 5)} --> {timestamp((i + 1) * 5)}\n{texts[i % 2]}"
        for i in range(500)
    ).encode("utf-8")
    worker = CS50Executor(
        plan,
        workspace=workspace,
        transport=httpx.MockTransport(lambda req: httpx.Response(200, content=body)),
    )
    binding = worker.select(course="cs50_python", section="0")[0]
    worker.run(binding)
    input = bind_cs50_knowledge_input(plan, binding, workspace=workspace)
    manifest = workspace / "knowledge-input.v1.json"
    save_knowledge_manifest(CS50KnowledgeInputManifest(inputs=(input,)), manifest)
    chunks = build_cs50_knowledge_chunks(
        plan, input, KnowledgeSettings(), workspace=workspace
    )
    assert len(chunks) > 22
    assert (
        json.loads(manifest.read_text())["inputs"][0]["source_id"] == binding.source_id
    )
    monkeypatch.setattr(request.module, "ROOT", workspace)
    monkeypatch.setattr(request.module, "MANIFEST", manifest)
    return SimpleNamespace(workspace=workspace, manifest=manifest, chunks=chunks)
