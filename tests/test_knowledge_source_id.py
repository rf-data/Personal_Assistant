"""Exercise the actual deterministic consolidation functions without app/LLM imports."""

import __future__

import ast
import json
import socket
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.model_knowledge import data_knowledge as models
from src.model_knowledge.data_knowledge import TranscriptKnowledgeDocument
from src.utils import text_helper

LEGACY = {
    "transcript_url": "https://example.com/official.txt",
    "media_id": None,
    "chunks": [],
    "visual_candidates": [],
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def consolidate():
    path = (
        Path(__file__).resolve().parents[1]
        / "src/tools_knowledge/consolidate_knowledge.py"
    )
    module = ast.parse(path.read_text())
    functions = [node for node in module.body if isinstance(node, ast.FunctionDef)]
    namespace = {**vars(models), **vars(text_helper)}
    exec(
        compile(
            ast.Module(body=functions, type_ignores=[]),
            str(path),
            "exec",
            flags=__future__.annotations.compiler_flag,
        ),
        namespace,
    )
    return namespace["consolidate_knowledge"]


def test_constructor_retains_source_id():
    document = TranscriptKnowledgeDocument(**LEGACY, source_id="lecture_0")
    assert document.source_id == "lecture_0"
    assert document.model_dump()["source_id"] == "lecture_0"


def test_json_roundtrip(tmp_path):
    document = TranscriptKnowledgeDocument(**LEGACY, source_id="lecture_0")
    path = tmp_path / "extraction.json"
    path.write_text(document.model_dump_json(), encoding="utf-8")
    assert TranscriptKnowledgeDocument.model_validate_json(path.read_text()) == document


@pytest.mark.parametrize("source_fields", [{}, {"source_id": None}])
def test_legacy_json_loads_without_identity(tmp_path, source_fields):
    payload = {**LEGACY, **source_fields}
    path = tmp_path / "lecture_0_know_extract.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    document = TranscriptKnowledgeDocument.model_validate_json(path.read_text())
    assert document.source_id is None
    assert document.transcript_url == payload["transcript_url"]
    assert json.loads(path.read_text()) == payload  # no migration or inferred identity


def test_valid_identity_survives_consolidation(consolidate):
    payload = {
        **LEGACY,
        "source_id": "original_lecture",
        "chunks": [
            {
                "analysis": {
                    "chunk_id": "chunk_0000",
                    "relevant": True,
                    "needs_visual_context": False,
                },
                "extraction": {
                    "chunk_id": "chunk_0000",
                    "statements": [
                        {
                            "statement_id": "S1",
                            "text": "A set contains elements.",
                            "semantic_type": "definition",
                            "segment_ids": [0],
                            "start": 0.0,
                            "end": 2.0,
                        }
                    ],
                    "formulas": [],
                },
            }
        ],
    }
    document = TranscriptKnowledgeDocument.model_validate(payload)
    result = consolidate(document)
    assert result.source_id == "original_lecture"
    assert result.statements[0].text == "A set contains elements."
    assert result.statements[0].evidence[0].segment_ids == [0]
    assert result.statements[0].evidence[0].start == 0.0
    assert document.source_id == "original_lecture"


def test_missing_identity_fails_before_processing_even_with_url(consolidate):
    document = TranscriptKnowledgeDocument(**LEGACY)
    with pytest.raises(ValueError, match="requires a non-empty source_id"):
        consolidate(document)
    assert document.source_id is None


def test_verified_external_context_can_explicitly_restore_legacy_identity(consolidate):
    legacy = TranscriptKnowledgeDocument(**LEGACY)
    # A caller may supply verified identity; filename/URL guessing is not a resolver.
    resolved = TranscriptKnowledgeDocument.model_validate(
        {
            **legacy.model_dump(),
            "source_id": "verified_original_transcript",
        }
    )
    assert consolidate(resolved).source_id == "verified_original_transcript"
    assert legacy.source_id is None


@pytest.mark.parametrize("identity", ["", " ", "\n\t", 123])
def test_invalid_explicit_identity_rejected(identity):
    with pytest.raises(ValidationError):
        TranscriptKnowledgeDocument(**LEGACY, source_id=identity)
