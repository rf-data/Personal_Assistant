"""CS50 Python week 0 contract pilot; SRT contents and extraction are synthetic."""

import __future__

import ast
import hashlib
import json
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.model_discovery.cs50 import ResourceRole
from src.model_knowledge import data_knowledge as models
from src.model_knowledge.data_knowledge import TranscriptKnowledgeDocument
from src.model_transcribe.data_transcribe import TranscriptDocument
from src.tools_lecture.prepare_cs50 import discover_fixture_courses
from src.tools_transcribe.import_transcript import import_srt, save_imported_transcript
from src.utils import text_helper
from src.utils.latex_helper import normalize_math_text

ROOT = Path(__file__).resolve().parents[1]
SRT = "1\n00:00:00,000 --> 00:00:20,000\nA variable stores a value.\n\n2\n00:00:20,000 --> 00:00:50,000\nPrint displays a value.\nOn a second line.\n\n3\n00:00:50,000 --> 00:01:20,000\nAddition combines numbers.\n"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline integration only")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def production_functions(path, names=None, *, link_math=False):
    module = ast.parse(path.read_text())
    functions = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and (names is None or node.name in names)
    ]
    namespace = {**vars(models), **vars(text_helper)}
    if link_math:
        # Test-only linkage: production imports this from the wrong module.
        namespace["normalize_math_text"] = normalize_math_text
    exec(
        compile(
            ast.Module(body=functions, type_ignores=[]),
            str(path),
            "exec",
            flags=__future__.annotations.compiler_flag,
        ),
        namespace,
    )
    return namespace


@pytest.fixture
def pilot(tmp_path):
    fixture_root = ROOT / "docs/course_sources/cs50"
    originals = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in fixture_root.rglob("*.html")
    }
    courses = discover_fixture_courses(fixture_root / "manifest.json")
    course = next(course for course in courses if course.course_id == "cs50_python")
    subtitle = next(
        resource
        for resource in course.resources
        if resource.role == ResourceRole.SUBTITLES and resource.section_keys == ("0",)
    )
    assert (
        str(subtitle.original_url)
        == "https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt"
    )
    assert subtitle.language == "en"
    path = tmp_path / "cs50_python_week_0.synthetic.en.srt"
    path.write_text(SRT, encoding="utf-8")
    transcript = import_srt(
        path, language=subtitle.language, original_url=str(subtitle.original_url)
    )
    find = production_functions(
        ROOT / "src/tools_knowledge/find_knowledge.py",
        {
            "build_transcript_chunks",
            "enrich_chunks",
            "attach_chunk_provenance",
            "validate_extraction",
            "make_visual_candidate",
        },
    )
    consolidate = production_functions(
        ROOT / "src/tools_knowledge/consolidate_knowledge.py", link_math=True
    )
    yield transcript, find, consolidate["consolidate_knowledge"], tmp_path
    assert all(
        hashlib.sha256(path.read_bytes()).hexdigest() == digest
        for path, digest in originals.items()
    )


def synthetic_results(transcript, find):
    chunks = find["build_transcript_chunks"](
        SimpleNamespace(target_duration=45, overlap_segments=1), transcript
    )
    find["enrich_chunks"](chunks)
    results = []
    for index, chunk in enumerate(chunks):
        # Deliberately wrong placeholders must be replaced by actual chunk evidence.
        result = models.ChunkKnowledgeResult.model_validate(
            {
                "analysis": {
                    "chunk_id": "placeholder",
                    "relevant": True,
                    "needs_visual_context": True,
                    "visual_reason": "Synthetic review",
                },
                "extraction": {
                    "chunk_id": "placeholder",
                    "statements": [
                        {
                            "statement_id": f"S{index}",
                            "text": "Print displays a value.",
                            "semantic_type": "statement",
                            "segment_ids": [999],
                            "start": 999,
                            "end": 1000,
                        }
                    ],
                    "formulas": [
                        {
                            "expression_id": f"F{index}",
                            "plain_text": "a + b",
                            "latex": "a+b",
                            "expression_type": "calculation",
                            "segment_ids": [999],
                            "start": 999,
                            "end": 1000,
                        }
                    ],
                },
            }
        )
        find["attach_chunk_provenance"](result, chunk)
        find["validate_extraction"](result)
        results.append(result)
    return chunks, results


def test_import_and_chunking(pilot):
    transcript, find, _, _ = pilot
    assert transcript.language == transcript.provenance.language == "en"
    assert transcript.provenance.transcript_source.value == "official_subtitle"
    assert transcript.provenance.transcription_provider is None
    assert [
        (segment.seg_id, segment.start, segment.end) for segment in transcript.segments
    ] == [(0, 0.0, 20.0), (1, 20.0, 50.0), (2, 50.0, 80.0)]
    assert transcript.segments[1].text == "Print displays a value.\nOn a second line."
    before = transcript.model_dump_json()
    chunks, _ = synthetic_results(transcript, find)
    assert [
        (chunk.chunk_id, chunk.segment_ids, chunk.start, chunk.end) for chunk in chunks
    ] == [("chunk_0000", [0, 1], 0.0, 50.0), ("chunk_0001", [1, 2], 20.0, 80.0)]
    assert transcript.model_dump_json() == before
    assert TranscriptDocument.model_validate_json(before) == transcript


def test_json_and_deterministic_consolidation(pilot):
    transcript, find, consolidate, tmp_path = pilot
    chunks, results = synthetic_results(transcript, find)
    # Match the existing runner's name derivation; this ID explicitly denotes synthetic input.
    normalized_path = tmp_path / f"{Path(transcript.source).name}.json"
    save_imported_transcript(transcript, normalized_path)
    assert (
        TranscriptDocument.model_validate_json(normalized_path.read_text())
        == transcript
    )
    source_id = normalized_path.name.removesuffix(".json")
    document = TranscriptKnowledgeDocument(
        source_id=source_id,
        transcript_url=transcript.provenance.source_url,
        media_id=None,
        chunks=results,
        visual_candidates=[
            find["make_visual_candidate"](result, chunk)
            for result, chunk in zip(results, chunks, strict=True)
        ],
    )
    path = tmp_path / "synthetic_know_extract.json"
    path.write_text(document.model_dump_json(), encoding="utf-8")
    loaded = TranscriptKnowledgeDocument.model_validate_json(path.read_text())
    consolidated = consolidate(loaded)
    assert consolidated.source_id == source_id
    assert consolidated.transcript_url == transcript.provenance.source_url
    assert len(consolidated.statements) == len(consolidated.formulas) == 1
    for item in [consolidated.statements[0], consolidated.formulas[0]]:
        assert [
            (e.chunk_id, e.segment_ids, e.start, e.end, e.source) for e in item.evidence
        ] == [
            ("chunk_0000", [0, 1], 0.0, 50.0, "transcript"),
            ("chunk_0001", [1, 2], 20.0, 80.0, "transcript"),
        ]
    assert [(c.start, c.end) for c in consolidated.visual_candidates] == [
        (0.0, 50.0),
        (20.0, 80.0),
    ]
    assert consolidated.formulas[0].verification_status == "pending"


def test_language_and_official_provenance_do_not_survive_current_contract(pilot):
    transcript, find, consolidate, _ = pilot
    _, results = synthetic_results(transcript, find)
    document = TranscriptKnowledgeDocument(
        source_id="explicit_synthetic_pilot",
        transcript_url=transcript.provenance.source_url,
        media_id=None,
        chunks=results,
        visual_candidates=[],
    )
    consolidated = consolidate(document)
    for model in (document, consolidated):
        assert model.language is None
        assert model.transcript_provenance is None
    evidence = consolidated.statements[0].evidence[0]
    assert (
        evidence.source == "transcript"
    )  # modality, not official acquisition strategy
    assert "transcript_source" not in type(evidence).model_fields
    assert transcript.provenance.transcript_source.value == "official_subtitle"
    assert transcript.provenance.source_file  # retained only in source document


def test_legacy_missing_source_identity_is_blocked(pilot):
    transcript, find, consolidate, _ = pilot
    _, results = synthetic_results(transcript, find)
    payload = {
        "transcript_url": transcript.provenance.source_url,
        "media_id": None,
        "chunks": [result.model_dump(mode="json") for result in results],
        "visual_candidates": [],
    }
    legacy = TranscriptKnowledgeDocument.model_validate_json(json.dumps(payload))
    assert legacy.source_id is None
    with pytest.raises(ValueError, match="requires a non-empty source_id"):
        consolidate(legacy)


def test_formula_normalization_import_is_corrected(pilot):
    transcript, find, _, _ = pilot
    assert not hasattr(text_helper, "normalize_math_text")
    module = ast.parse(
        (ROOT / "src/tools_knowledge/consolidate_knowledge.py").read_text()
    )
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "src.utils.latex_helper"
        and any(alias.name == "normalize_math_text" for alias in node.names)
        for node in module.body
    )
    production = production_functions(
        ROOT / "src/tools_knowledge/consolidate_knowledge.py", link_math=True
    )
    _, results = synthetic_results(transcript, find)
    document = TranscriptKnowledgeDocument(
        source_id="explicit_synthetic_pilot",
        transcript_url=transcript.provenance.source_url,
        media_id=None,
        chunks=results,
        visual_candidates=[],
    )
    assert len(production["consolidate_knowledge"](document).formulas) == 1
