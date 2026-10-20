"""Checked SRT → actual chunk/evidence functions → real deterministic consolidation."""

import importlib
import json
import socket
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRT = b"1\n00:00:01,000 --> 00:00:02,000\nValue\n\n2\n00:00:03,000 --> 00:00:04,000\n\n3\n00:00:05,000 --> 00:00:06,000\nAnother value\n"


@pytest.fixture(scope="module")
def context(tmp_path_factory):
    before = set(sys.modules)
    directory = tmp_path_factory.mktemp("knowledge-settings")
    with pytest.MonkeyPatch.context() as patch:
        patch.chdir(directory)
        for key, value in {
            "ROOT": str(directory),
            "CHROMA_DIR": str(directory / "chroma"),
            "DATA_DIR": str(directory / "data"),
            "WIKI_EN_API": "https://example.invalid",
            "HEADER_AGENT": "offline",
            "HF_API_KEY": "offline",
            "OPENAI_API_KEY": "offline",
        }.items():
            patch.setenv(key, value)

        def forbidden(*args, **kwargs):
            raise AssertionError("Network forbidden")

        patch.setattr(socket.socket, "connect", forbidden)
        patch.setattr(socket, "getaddrinfo", forbidden)
        module = importlib.import_module("src.tools_knowledge.bind_cs50_transcript")
        executor = importlib.import_module("src.tools_lecture.execute_cs50")
        consolidation = importlib.import_module(
            "src.tools_knowledge.consolidate_knowledge"
        )
        plan = module.CS50AdapterPlan.model_validate_json(
            (ROOT / "docs/course_sources/cs50/cs50_lecture_plan.v1.json").read_bytes()
        )
        yield module, executor, consolidation, plan
        assert "marvin" not in sys.modules
    for name in list(sys.modules):
        if name not in before and name.startswith("src."):
            sys.modules.pop(name, None)


def imported(context, tmp_path, course="cs50_python", body=SRT):
    module, executor, consolidation, plan = context
    worker = executor.CS50Executor(
        plan,
        workspace=tmp_path,
        transport=httpx.MockTransport(lambda req: httpx.Response(200, content=body)),
    )
    binding = worker.select(course=course, section="0")[0]
    worker.run(binding)
    return binding, module.bind_cs50_knowledge_input(plan, binding, workspace=tmp_path)


def synthetic(chunk):
    from src.model_knowledge.data_knowledge import ChunkKnowledgeResult

    return ChunkKnowledgeResult.model_validate(
        {
            "analysis": {
                "chunk_id": chunk.chunk_id,
                "relevant": True,
                "needs_visual_context": False,
            },
            "extraction": {
                "chunk_id": chunk.chunk_id,
                "statements": [
                    {
                        "statement_id": "S1",
                        "text": "Synthetic value claim",
                        "semantic_type": "statement",
                        "segment_ids": [],
                        "start": 999,
                        "end": 999,
                    }
                ],
                "formulas": [
                    {
                        "expression_id": "F1",
                        "plain_text": "x = 1",
                        "latex": "x = 1",
                        "expression_type": "equation",
                        "segment_ids": [],
                        "start": 999,
                        "end": 999,
                    }
                ],
            },
        }
    )


@pytest.mark.parametrize("course", ["cs50_python", "cs50_cybersecurity"])
def test_end_to_end(context, tmp_path, course):
    module, executor, consolidation, plan = context
    binding, input = imported(context, tmp_path, course)
    from src.core.config_knowledge import KnowledgeSettings

    chunks = module.build_cs50_knowledge_chunks(
        plan, input, KnowledgeSettings(), workspace=tmp_path
    )
    assert all(1 not in chunk.segment_ids for chunk in chunks)
    assert (
        chunks[0].segment_ids == [0, 2] and chunks[0].start == 1 and chunks[0].end == 6
    )
    document = module.build_cs50_knowledge_document(
        input, chunks, [synthetic(chunks[0])], plan=plan, workspace=tmp_path
    )
    extraction_path = tmp_path / "synthetic-extraction.json"
    with extraction_path.open("x") as output:
        output.write(document.model_dump_json())
    document = type(document).model_validate_json(extraction_path.read_bytes())
    result = consolidation.consolidate_knowledge(document)
    result_path = tmp_path / "synthetic-consolidated.json"
    with result_path.open("x") as output:
        output.write(result.model_dump_json())
    loaded = type(result).model_validate_json(result_path.read_bytes())
    assert loaded == result
    for field in (
        "source_id",
        "transcript_url",
        "language",
        "transcript_provenance",
        "course_id",
        "lecture_id",
        "media_id",
    ):
        assert getattr(result, field) == getattr(input, field)
    assert result.statements[0].evidence[0].segment_ids == [0, 2]
    assert result.formulas[0].evidence[0].chunk_id == chunks[0].chunk_id
    assert result.formulas[0].evidence[0].start == 1
    assert result.statements[0].evidence[0].source == "transcript"
    if course == "cs50_cybersecurity":
        assert input.media_id is None
    manifest = module.CS50KnowledgeInputManifest(inputs=(input,))
    path = tmp_path / "input.v1.json"
    module.save_knowledge_manifest(manifest, path)
    assert (
        module.CS50KnowledgeInputManifest.model_validate_json(path.read_bytes())
        == manifest
    )
    with pytest.raises(FileExistsError):
        module.save_knowledge_manifest(manifest, path)


@pytest.mark.parametrize(
    "failure",
    ["missing", "version", "running", "download", "hash", "provenance", "input_hash"],
)
def test_bad_receipt(context, tmp_path, failure):
    module, executor, consolidation, plan = context
    binding, input = imported(context, tmp_path)
    receipt = input.receipt_path
    state = json.loads(receipt.read_text())
    if failure == "missing":
        receipt.unlink()
    else:
        if failure == "version":
            state["schema_version"] = 2
        elif failure == "provenance":
            state["binding"]["language"] = "fr"
        else:
            records = list(state["actions"].values())
            if failure == "running":
                records[1]["status"] = "prepared"
            if failure == "download":
                records[0]["status"] = "failed"
            if failure == "hash":
                records[1]["sha256"] = "0" * 64
            if failure == "input_hash":
                records[1]["input_sha256"] = "0" * 64
        receipt.write_text(json.dumps(state))
    with pytest.raises(executor.ExecutionConflict):
        module.bind_cs50_knowledge_input(plan, binding, workspace=tmp_path)


def test_all_50_contracts_without_processing(context):
    module, executor, consolidation, plan = context
    bindings = [b for c in plan.courses for b in c.bindings]
    assert len(bindings) == 50 and len({b.source_id for b in bindings}) == 50
    assert len({b.course_id for b in bindings}) == 6
    assert all(b.source_id == b.resource_id != b.lecture_id for b in bindings)
    assert all(b.language == "en" and b.format == "srt" for b in bindings)
    assert any(b.section_key == "ai" for b in bindings)


def test_real_local_pilot(context, tmp_path):
    module, executor, consolidation, plan = context
    binding = next(
        b
        for c in plan.courses
        for b in c.bindings
        if b.course_id == "cs50_python" and b.section_key == "0"
    )
    if not (ROOT / binding.raw_srt_path).exists():
        pytest.skip("Imported original pilot unavailable")
    input = module.bind_cs50_knowledge_input(plan, binding, workspace=ROOT)
    from src.core.config_knowledge import KnowledgeSettings

    chunks = module.build_cs50_knowledge_chunks(
        plan, input, KnowledgeSettings(), workspace=ROOT
    )
    document = module.build_cs50_knowledge_document(
        input, chunks[:1], [synthetic(chunks[0])], plan=plan, workspace=ROOT
    )
    result = consolidation.consolidate_knowledge(document)
    assert result.source_id == binding.source_id
    assert result.transcript_provenance == input.transcript_provenance
    assert result.formulas and result.statements
    for name, value in (
        ("pilot-extraction", document),
        ("pilot-consolidation", result),
    ):
        path = tmp_path / f"{name}.json"
        with path.open("x", encoding="utf-8") as output:
            output.write(value.model_dump_json())
        assert type(value).model_validate_json(path.read_bytes()) == value


def test_legacy_json_and_unknown_result(context, tmp_path):
    module, executor, consolidation, plan = context
    legacy = module.TranscriptKnowledgeDocument.model_validate(
        {
            "transcript_url": None,
            "media_id": None,
            "chunks": [],
            "visual_candidates": [],
        }
    )
    assert legacy.source_id is None
    with pytest.raises(ValueError, match="source_id"):
        consolidation.consolidate_knowledge(legacy)
    binding, input = imported(context, tmp_path)
    from src.core.config_knowledge import KnowledgeSettings

    chunks = module.build_cs50_knowledge_chunks(
        plan, input, KnowledgeSettings(), workspace=tmp_path
    )
    supplied = synthetic(chunks[0])
    supplied.analysis.chunk_id = "unverified"
    with pytest.raises(executor.ExecutionConflict):
        module.build_cs50_knowledge_document(
            input, chunks, [supplied], plan=plan, workspace=tmp_path
        )


def test_provenance_contents_not_only_receipt(context, tmp_path):
    module, executor, consolidation, plan = context
    binding, input = imported(context, tmp_path)
    document = json.loads(input.transcript_json_path.read_text())
    document["provenance"]["source_url"] = "https://example.invalid/other.srt"
    input.transcript_json_path.write_text(json.dumps(document))
    receipt = json.loads(input.receipt_path.read_text())
    for record in receipt["actions"].values():
        if record["action"] == "parse_subtitle":
            record["sha256"] = executor.digest(input.transcript_json_path)
    input.receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(executor.ExecutionConflict, match="provenance"):
        module.bind_cs50_knowledge_input(plan, binding, workspace=tmp_path)


def test_empty_cue_cannot_be_evidence(context, tmp_path):
    module, executor, consolidation, plan = context
    binding, input = imported(context, tmp_path)
    from src.core.config_knowledge import KnowledgeSettings

    chunks = module.build_cs50_knowledge_chunks(
        plan, input, KnowledgeSettings(), workspace=tmp_path
    )
    forged = chunks[0].model_copy(update={"segment_ids": [1]})
    with pytest.raises(executor.ExecutionConflict, match="empty cue"):
        module.build_cs50_knowledge_document(
            input, [forged], [synthetic(forged)], plan=plan, workspace=tmp_path
        )


def test_fresh_import_blocks_even_marvin_attempt(context, tmp_path):
    import os
    import subprocess

    env = dict(os.environ)
    env.update(
        {
            "ROOT": str(tmp_path),
            "CHROMA_DIR": str(tmp_path / "chroma"),
            "DATA_DIR": str(tmp_path / "data"),
            "WIKI_EN_API": "https://example.invalid",
            "HEADER_AGENT": "offline",
            "HF_API_KEY": "offline",
            "OPENAI_API_KEY": "offline",
        }
    )
    code = f"""
import sys, importlib.abc, socket
sys.path.insert(0, {str(ROOT)!r})
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in ('marvin', 'faster_whisper', 'yt_dlp'):
            raise AssertionError('Forbidden initialization: ' + fullname)
sys.meta_path.insert(0, Guard())
def forbidden(*args, **kwargs):
    raise AssertionError('Network forbidden')
socket.socket.connect = forbidden
socket.getaddrinfo = forbidden
import src.tools_knowledge.bind_cs50_transcript
import src.tools_knowledge.consolidate_knowledge
print('real offline import passed')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        env=env,
        cwd=tmp_path,
        timeout=30,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "real offline import passed" in result.stdout


@pytest.mark.parametrize(
    "field,value",
    [
        ("course_id", "other"),
        ("lecture_id", "other"),
        ("source_id", "other"),
        ("resource_id", "other"),
        ("section_key", "1"),
        ("language", "fr"),
        ("media_id", "invented"),
    ],
)
def test_manifest_rejects_identity_conflicts(context, tmp_path, field, value):
    module, executor, consolidation, plan = context
    binding, input = imported(context, tmp_path)
    payload = input.model_dump()
    payload[field] = value
    with pytest.raises(ValueError, match="contradicts binding"):
        module.CS50KnowledgeInput.model_validate(payload)


@pytest.mark.parametrize("path_field", ["raw_srt_path", "transcript_json_path"])
def test_missing_artifact(context, tmp_path, path_field):
    module, executor, consolidation, plan = context
    binding, input = imported(context, tmp_path)
    getattr(input, path_field).unlink()
    with pytest.raises(executor.ExecutionConflict, match="Missing artifact"):
        module.bind_cs50_knowledge_input(plan, binding, workspace=tmp_path)


@pytest.mark.parametrize("field", ["raw_sha256", "transcript_sha256"])
def test_manifest_requires_sha256(context, tmp_path, field):
    module, executor, consolidation, plan = context
    binding, input = imported(context, tmp_path)
    payload = input.model_dump()
    payload[field] = "not-a-sha256"
    with pytest.raises(ValueError):
        module.CS50KnowledgeInput.model_validate(payload)


def test_visual_candidate_only_no_visual_processing(context, tmp_path):
    module, executor, consolidation, plan = context
    binding, input = imported(context, tmp_path)
    from src.core.config_knowledge import KnowledgeSettings

    chunks = module.build_cs50_knowledge_chunks(
        plan, input, KnowledgeSettings(), workspace=tmp_path
    )
    supplied = synthetic(chunks[0])
    supplied.analysis.needs_visual_context = True
    supplied.analysis.visual_reason = "synthetic visual requirement"
    document = module.build_cs50_knowledge_document(
        input, chunks, [supplied], plan=plan, workspace=tmp_path
    )
    result = consolidation.consolidate_knowledge(document)
    assert result.visual_candidates == document.visual_candidates
    assert result.visual_candidates[0].segment_ids == [0, 2]
    assert result.visual_candidates[0].start == 1
    assert result.formulas[0].verification_status == "pending"


def test_receipt_rechecked_before_document(context, tmp_path):
    module, executor, consolidation, plan = context
    binding, input = imported(context, tmp_path)
    from src.core.config_knowledge import KnowledgeSettings

    chunks = module.build_cs50_knowledge_chunks(
        plan, input, KnowledgeSettings(), workspace=tmp_path
    )
    receipt = json.loads(input.receipt_path.read_text())
    next(iter(receipt["actions"].values()))["status"] = "failed"
    input.receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(executor.ExecutionConflict, match="not successfully completed"):
        module.build_cs50_knowledge_document(
            input, chunks, [synthetic(chunks[0])], plan=plan, workspace=tmp_path
        )
