"""Actual pipeline function bodies with local synthetic extraction/agent boundaries."""

import __future__

import ast
import json
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
def test_metadata_roundtrip_for_all_supported_origins(kind, metadata_model):
    model, payload = metadata_model
    document = model(
        **payload,
        source_id="verified_source",
        language="en",
        transcript_provenance=provenance(kind),
        course_id="course",
        lecture_id="0",
        transcript_url="https://example.com/official.srt",
        media_id=None,
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
    with pytest.raises(ValidationError, match="contradicts transcript_provenance"):
        model.model_validate_json(
            json.dumps(
                {**payload, "transcript_provenance": prov.model_dump(mode="json")}
            )
        )


@pytest.fixture(
    params=[
        models.TranscriptKnowledgeDocument,
        models.ConsolidatedKnowledgeDocument,
        models.LectureKnowledgeDocument,
    ],
    ids=lambda model: model.__name__,
)
def metadata_model(request):
    model = request.param
    payload = (
        {"chunks": [], "visual_candidates": []}
        if model is models.TranscriptKnowledgeDocument
        else {"stats": {}}
    )
    return model, payload


def test_shared_metadata_contract_roundtrip(metadata_model):
    model, payload = metadata_model
    prov = provenance().model_copy(update={"media_id": "media"})
    values = dict(
        source_id="verified-source",
        language="en",
        transcript_url=prov.source_url,
        transcript_provenance=prov,
        media_id="media",
        course_id="verified-course",
        lecture_id="ai",
    )
    document = model(**payload, **values)
    assert set(values) <= set(model.model_fields)
    assert document.transcript_metadata() == {
        name: values[name]
        for name in ("language", "transcript_provenance", "course_id", "lecture_id")
    }
    assert all(getattr(document, name) == value for name, value in values.items())
    assert model.model_validate_json(document.model_dump_json()) == document
    assert model.model_validate(document.model_dump()) == document
    assert document.model_dump()["source_id"] == "verified-source"


def test_provenance_does_not_fill_unknown_document_fields(metadata_model):
    model, payload = metadata_model
    prov = provenance().model_copy(update={"media_id": "proven-media"})
    document = model(**payload, source_id="verified", transcript_provenance=prov)
    for name in ("language", "transcript_url", "media_id", "course_id", "lecture_id"):
        assert getattr(document, name) is None
    assert document.source_id == "verified"
    assert model.model_validate_json(document.model_dump_json()) == document


def test_missing_provenance_values_do_not_contradict_document(metadata_model):
    model, payload = metadata_model
    prov = TranscriptProvenance(
        transcript_source=TranscriptSource.WHISPER,
        source_file="local/audio.mp3",
    )
    document = model(
        **payload,
        source_id="verified",
        language="de",
        transcript_url="https://example.com/media",
        media_id="media",
        transcript_provenance=prov,
    )
    assert document.language == "de"
    assert document.transcript_provenance.language is None
    assert model.model_validate_json(document.model_dump_json()) == document


def test_completely_absent_metadata_preserves_identity_contract(metadata_model):
    model, payload = metadata_model
    if model is models.TranscriptKnowledgeDocument:
        document = model(**payload)
        assert document.source_id is None
        for identity in ("", " ", "\n\t", 123):
            with pytest.raises(ValidationError):
                model(**payload, source_id=identity)
    else:
        for identity in ({}, {"source_id": None}, {"source_id": 123}):
            with pytest.raises(ValidationError):
                model(**payload, **identity)
        # Preserve the existing plain-str contract of consolidated documents.
        assert model(**payload, source_id="").source_id == ""
        document = model(**payload, source_id="verified")
    for name in (
        "language",
        "transcript_url",
        "transcript_provenance",
        "media_id",
        "course_id",
        "lecture_id",
    ):
        assert getattr(document, name) is None
    assert model.model_validate_json(document.model_dump_json()) == document
