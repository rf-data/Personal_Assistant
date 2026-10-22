"""Compiler and constructor regressions; no SDK execution or real source inputs."""

import socket
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_knowledge_transcript_provenance import (
    extraction,
    functions,
    provenance,
    semantic,
)

from src.model_knowledge.data_knowledge import TranscriptKnowledgeDocument
from src.model_transcribe.data_transcribe import TranscriptDocument, TranscriptSegment
from src.tools_knowledge.consolidate_knowledge import consolidate_knowledge

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("No network or real provider allowed")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.mark.parametrize(
    "name",
    [
        "src/run_knowledge_extraction.py",
        "src/tools_knowledge/consolidate_knowledge.py",
        "src/tools_knowledge/semantic_knowledge.py",
    ],
)
def test_production_modules_compile_without_executing_imports(name):
    # ast.parse alone accepts repeated literal keywords; compile rejects them.
    path = ROOT / name
    compile(path.read_text(), str(path), "exec")


@pytest.mark.parametrize("with_statements", [False, True])
@pytest.mark.parametrize("media_id", [None, "synthetic-media"])
def test_distinct_identities_survive_both_semantic_branches(with_statements, media_id):
    prov = provenance().model_copy(update={"media_id": media_id})
    document = TranscriptKnowledgeDocument(
        source_id="synthetic-source",
        lecture_id="synthetic-lecture",
        course_id="synthetic-course",
        media_id=media_id,
        transcript_url=prov.source_url,
        language=prov.language,
        transcript_provenance=prov,
        chunks=[extraction()] if with_statements else [],
        visual_candidates=[],
    )
    before = document.model_dump_json()
    deterministic = consolidate_knowledge(document)
    assert bool(deterministic.statements) == with_statements
    final = semantic(deterministic)  # Existing harness substitutes agent boundaries.
    for stage in (deterministic, final):
        assert stage.source_id == "synthetic-source"
        assert stage.lecture_id == "synthetic-lecture"
        assert stage.course_id == "synthetic-course"
        assert stage.media_id == media_id
        assert stage.transcript_url == prov.source_url
        assert stage.transcript_metadata() == document.transcript_metadata()
        assert type(stage).model_validate_json(stage.model_dump_json()) == stage
    assert document.model_dump_json() == before


def test_extraction_preserves_explicit_lecture_and_separate_source_and_media():
    prov = provenance().model_copy(update={"media_id": "synthetic-media"})
    transcript = TranscriptDocument(
        source="synthetic.srt",
        language="en",
        provenance=prov,
        segments=[TranscriptSegment(seg_id=7, start=0, end=50, text="Synthetic.")],
        text="Synthetic.",
    )
    before = transcript.model_dump_json()
    find = functions(
        "src/tools_knowledge/find_knowledge.py",
        {
            "build_transcript_chunks",
            "enrich_chunks",
            "attach_chunk_provenance",
            "validate_extraction",
            "make_visual_candidate",
        },
    )
    runner = functions(
        "src/run_knowledge_extraction.py",
        {"knowledge_extraction"},
        **find,
        load_dict=lambda **_: transcript,
        configure_marvin=lambda _: None,
        extract_media_id=lambda _: "synthetic-media",
        analyze_chunk_with_retry=lambda *_: extraction(),
    )["knowledge_extraction"]
    context = SimpleNamespace(
        course_id="synthetic-course",
        lecture_id="synthetic-lecture",
        cfg_knowledge=SimpleNamespace(
            target_duration=45, overlap_segments=1, llm_model="synthetic-only"
        ),
    )
    result = runner(context, Path("synthetic-source.json"))
    assert result.source_id == "synthetic-source"
    assert result.lecture_id == "synthetic-lecture"
    assert result.media_id == "synthetic-media"
    assert result.course_id == "synthetic-course"
    assert result.transcript_provenance == prov
    assert result.chunks[0].extraction.statements[0].segment_ids == [7]
    assert transcript.model_dump_json() == before
