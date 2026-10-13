"""Actual pipeline function bodies with local synthetic extraction/agent boundaries."""

import __future__

import ast
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.model_knowledge import data_knowledge as models
from src.model_transcribe.data_transcribe import (
    TranscriptDocument,
    TranscriptProvenance,
    TranscriptSegment,
    TranscriptSource,
)
from src.utils import text_helper
from src.utils.latex_helper import normalize_math_text

ROOT = Path(__file__).resolve().parents[1]


def functions(name, selected=None, **extra):
    path = ROOT / name
    module = ast.parse(path.read_text())
    nodes = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and (selected is None or node.name in selected)
    ]
    namespace = {
        **vars(models),
        **vars(text_helper),
        "normalize_math_text": normalize_math_text,
        "Path": Path,
        "TranscriptDocument": TranscriptDocument,
        **extra,
    }
    exec(
        compile(
            ast.Module(body=nodes, type_ignores=[]),
            str(path),
            "exec",
            flags=__future__.annotations.compiler_flag,
        ),
        namespace,
    )
    return namespace


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No networking")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def provenance(kind=None):
    kind = kind or TranscriptSource.__members__.get(
        "OFFICIAL_SUBTITLE", TranscriptSource.MANUAL_SUBTITLE
    )
    return TranscriptProvenance(
        transcript_source=kind,
        language="en",
        source_url="https://example.com/official.srt",
        source_file="local/official.srt",
        media_format="srt",
    )


def extraction():
    return models.ChunkKnowledgeResult.model_validate(
        {
            "analysis": {
                "chunk_id": "placeholder",
                "relevant": True,
                "needs_visual_context": False,
            },
            "extraction": {
                "chunk_id": "placeholder",
                "statements": [
                    {
                        "statement_id": "S1",
                        "text": "A variable stores a value.",
                        "semantic_type": "statement",
                        "segment_ids": [99],
                        "start": 999,
                        "end": 999,
                    }
                ],
                "formulas": [],
            },
        }
    )


def run_extraction():
    transcript = TranscriptDocument(
        source="local/official.srt",
        language="en",
        provenance=provenance(),
        segments=[
            TranscriptSegment(
                seg_id=7, start=0, end=50, text="A variable stores a value."
            )
        ],
        text="A variable stores a value.",
    )
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
        load_dict=lambda **kwargs: transcript,
        configure_marvin=lambda config: None,
        extract_media_id=lambda url: None,
        analyze_chunk_with_retry=lambda *args: extraction(),
    )
    context = SimpleNamespace(
        course_id="verified_course",
        cfg_knowledge=SimpleNamespace(
            target_duration=45, overlap_segments=1, llm_model="synthetic-only"
        ),
    )
    return runner["knowledge_extraction"](
        context, Path("original_transcript.json")
    ), transcript


def consolidate(document):
    return functions("src/tools_knowledge/consolidate_knowledge.py")[
        "consolidate_knowledge"
    ](document)


def semantic(document):
    namespace = functions(
        "src/tools_knowledge/semantic_knowledge.py",
        marvin=SimpleNamespace(Agent=lambda **kwargs: SimpleNamespace()),
        app_session=SimpleNamespace(logger=None),
        SEMANTIC_CONSOLIDATION_PROMPT="",
        ENTITY_EXTRACTION_PROMPT="",
    )
    namespace["consolidate_semantic_batch"] = lambda **kwargs: SimpleNamespace(
        canonical_statements=[], discarded_statements=[]
    )
    namespace["extract_entity_batch"] = lambda **kwargs: SimpleNamespace()
    namespace["merge_lecture_entities"] = lambda results: []
    return namespace["consolidate_semantic_knowledge"](
        document, model_name="synthetic-only"
    )


@pytest.mark.parametrize("kind", list(TranscriptSource))
def test_metadata_roundtrip_for_all_supported_origins(kind):
    document = models.TranscriptKnowledgeDocument(
        source_id="verified_source",
        language="en",
        transcript_provenance=provenance(kind),
        course_id="course",
        lecture_id="0",
        transcript_url="https://example.com/official.srt",
        media_id=None,
        chunks=[],
        visual_candidates=[],
    )
    assert type(document).model_validate_json(document.model_dump_json()) == document
    assert document.transcript_provenance.transcript_source == kind


def test_real_extraction_and_deterministic_and_semantic_contracts():
    document, transcript = run_extraction()
    deterministic = consolidate(document)
    final = semantic(deterministic)
    assert (
        document.source_id
        == deterministic.source_id
        == final.source_id
        == "original_transcript"
    )
    for stage in (document, deterministic, final):
        assert stage.language == "en"
        assert stage.course_id == "verified_course"
        assert stage.lecture_id is None  # context has no verified lecture identity
        assert stage.transcript_provenance == transcript.provenance
        assert stage.transcript_url == transcript.provenance.source_url
        assert type(stage).model_validate_json(stage.model_dump_json()) == stage
    for item in [deterministic.statements[0], final.statements[0]]:
        evidence = item.evidence[0]
        assert (
            evidence.chunk_id,
            evidence.segment_ids,
            evidence.start,
            evidence.end,
            evidence.source,
        ) == ("chunk_0000", [7], 0.0, 50.0, "transcript")


def test_semantic_no_statements_branch_preserves_explicit_assignment_and_media():
    document = models.ConsolidatedKnowledgeDocument(
        source_id="source",
        language="en",
        transcript_provenance=provenance(),
        course_id="course",
        lecture_id="week_0",
        media_id="verified_media",
        stats=models.ConsolidationStats(),
    )
    final = semantic(document)
    assert final.transcript_metadata() == document.transcript_metadata()
    assert final.media_id == "verified_media"
    assert final.transcript_url is None  # do not fill from provenance implicitly


@pytest.mark.parametrize(
    "model,payload",
    [
        (
            models.TranscriptKnowledgeDocument,
            {
                "transcript_url": None,
                "media_id": None,
                "chunks": [],
                "visual_candidates": [],
            },
        ),
        (models.ConsolidatedKnowledgeDocument, {"source_id": "legacy", "stats": {}}),
        (models.LectureKnowledgeDocument, {"source_id": "legacy", "stats": {}}),
    ],
)
def test_legacy_documents_without_new_metadata(model, payload):
    document = model.model_validate(payload)
    assert all(value is None for value in document.transcript_metadata().values())
    assert model.model_validate_json(document.model_dump_json()) == document


@pytest.mark.parametrize(
    "field,value",
    [
        ("language", "de"),
        ("transcript_url", "https://example.com/other.srt"),
        ("media_id", "different_media"),
    ],
)
@pytest.mark.parametrize(
    "model",
    [
        models.TranscriptKnowledgeDocument,
        models.ConsolidatedKnowledgeDocument,
        models.LectureKnowledgeDocument,
    ],
)
def test_contradictory_provenance_rejected(model, field, value):
    prov = provenance().model_copy(update={"media_id": "verified_media"})
    payload = {
        "source_id": "source",
        "language": "en",
        "transcript_provenance": prov,
        "transcript_url": prov.source_url,
        "media_id": "verified_media",
        "chunks": [],
        "visual_candidates": [],
        "stats": {},
        field: value,
    }
    with pytest.raises(ValidationError, match="contradicts transcript_provenance"):
        model.model_validate(payload)
