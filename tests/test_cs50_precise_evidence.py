"""Cue-reference validation and integration; no inference or artificial timestamps."""

import copy
import json

import httpx
import pytest
from test_cs50_knowledge_pilot import MANIFEST, PLAN, ROOT
from test_cs50_knowledge_pilot import controlled_settings as controlled_settings

from scripts import cs50_knowledge_pilot as cli
from src.model_knowledge.data_knowledge import TranscriptChunk
from src.model_transcribe.data_transcribe import TranscriptSegment
from src.tools_knowledge.cs50_extraction_provider import (
    messages_for,
)
from src.tools_knowledge.cs50_precise_evidence import (
    EvidenceValidationError,
    bind_precise_candidates,
)


def fixture():
    segments = {
        10: TranscriptSegment(seg_id=10, start=1, end=2, text="Python input"),
        11: TranscriptSegment(seg_id=11, start=3, end=4, text="input accepts a prompt"),
        12: TranscriptSegment(seg_id=12, start=5, end=6, text="x = 1"),
        13: TranscriptSegment(seg_id=13, start=7, end=8, text=""),
    }
    chunk = TranscriptChunk(
        chunk_id="chunk_0000",
        segment_ids=[10, 11, 12],
        start=1,
        end=6,
        text="Python input\ninput accepts a prompt\nx = 1",
        n_words=9,
    )
    raw = {
        "analysis": {"chunk_id": chunk.chunk_id, "relevant": True},
        "extraction": {
            "chunk_id": chunk.chunk_id,
            "statements": [
                {
                    "statement_id": "S1",
                    "text": "Python input",
                    "semantic_type": "statement",
                    "segment_ids": [10],
                },
                {
                    "statement_id": "S2",
                    "text": "input accepts a prompt",
                    "semantic_type": "statement",
                    "segment_ids": [11],
                },
            ],
            "formulas": [
                {
                    "expression_id": "F1",
                    "plain_text": "x = 1",
                    "expression_type": "equation",
                    "segment_ids": [12],
                }
            ],
        },
    }
    return segments, chunk, raw


def test_distinct_precise_evidence_and_roundtrip():
    segments, chunk, raw = fixture()
    before = copy.deepcopy(raw)
    audit = []
    result = bind_precise_candidates(raw, chunk, segments, audit)
    assert raw == before
    assert [s.start for s in result.extraction.statements] == [1, 3]
    assert result.extraction.formulas[0].start == 5
    assert result.extraction.formulas[0].segment_ids == [12]
    assert len(audit) == 3 and all(a["scope"] == "statement_precise" for a in audit)
    assert type(result).model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize("ids", [[], [999], [13], [10, 10], ["10"], [True]])
def test_invalid_references(ids):
    segments, chunk, raw = fixture()
    raw["extraction"]["statements"][0]["segment_ids"] = ids
    with pytest.raises(EvidenceValidationError) as error:
        bind_precise_candidates(raw, chunk, segments)
    assert error.value.audit[-1]["scope"] == "invalid"


@pytest.mark.parametrize("path", ["analysis", "extraction", "source", "item_source"])
def test_foreign_context(path):
    segments, chunk, raw = fixture()
    if path in ("analysis", "extraction"):
        raw[path]["chunk_id"] = "foreign"
    elif path == "source":
        raw["source_id"] = "foreign"
    else:
        raw["extraction"]["statements"][0]["source"] = "visual"
    with pytest.raises(EvidenceValidationError):
        bind_precise_candidates(raw, chunk, segments)


def test_model_times_ignored():
    segments, chunk, raw = fixture()
    raw["extraction"]["statements"][0].update(start=999, end=-10)
    result = bind_precise_candidates(raw, chunk, segments)
    assert (
        result.extraction.statements[0].start,
        result.extraction.statements[0].end,
    ) == (1, 2)


def test_prompt_input_and_legacy_unchanged():
    segments, chunk, raw = fixture()
    legacy = messages_for(chunk)
    precise = messages_for(chunk, segments=segments)
    assert precise[0] == legacy[0]  # same relevance instructions
    payload = json.loads(precise[1]["content"])
    assert payload["input_version"] == "cs50_segment_evidence_v1"
    assert [s["seg_id"] for s in payload["segments"]] == [10, 11, 12]
    assert "start" not in payload["schema"]["$defs"]["KnowledgeStatement"]["properties"]
    assert messages_for(chunk) == legacy


def test_full_pilot_preserves_source_and_consolidates(
    controlled_settings, tmp_path, monkeypatch
):
    from src.tools_knowledge import cs50_extraction_provider as providers

    original = providers.OpenAIHTTPProvider

    def handle(request):
        payload = json.loads(request.content)
        data = json.loads(payload["messages"][1]["content"])
        cues = data["segments"]
        cid = data["chunk_id"]
        raw = {
            "analysis": {"chunk_id": cid, "relevant": True},
            "extraction": {
                "chunk_id": cid,
                "statements": [
                    {
                        "statement_id": str(i),
                        "text": cues[i]["text"],
                        "semantic_type": "statement",
                        "segment_ids": [cues[i]["seg_id"]],
                    }
                    for i in [0, 1]
                ],
                "formulas": [],
            },
        }
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"content": json.dumps(raw)}}
                ]
            },
        )

    monkeypatch.setattr(
        providers,
        "OpenAIHTTPProvider",
        lambda **kw: original(**kw, transport=httpx.MockTransport(handle)),
    )
    monkeypatch.setenv("CS50_KNOWLEDGE_EXECUTE_LLM", "1")
    config = {
        "execute_llm": True,
        "provider": "openai_http",
        "model": "fake",
        "probe_marvin": False,
        "plan": str(PLAN),
        "manifest": str(MANIFEST),
        "workspace": str(ROOT),
        "max_chunks": 1,
        "chunk_index": 20,
        "evidence_mode": "segment_v1",
        "token_budget": 60000,
        "input_limit": 28000,
        "output_limit": 1200,
    }
    cli.save(tmp_path / "configuration.json", config)
    assert cli.worker(tmp_path / "configuration.json") == 0
    document = json.loads((tmp_path / "extraction.json").read_text())
    expected = json.loads(MANIFEST.read_text())["inputs"][0]
    for field in (
        "source_id",
        "lecture_id",
        "course_id",
        "transcript_provenance",
        "transcript_url",
        "media_id",
        "language",
    ):
        assert document[field] == expected[field]
    statements = document["chunks"][0]["extraction"]["statements"]
    assert statements[0]["segment_ids"] != statements[1]["segment_ids"]
    scopes = json.loads((tmp_path / "quality_report.json").read_text())[
        "evidence_scope_counts"
    ]
    assert scopes == {"statement_precise": 2}
    raw = json.loads((tmp_path / "chunk_0020.provider.json").read_text())
    assert "start" not in raw["extraction"]["statements"][0]
    consolidated = json.loads((tmp_path / "consolidated.json").read_text())
    assert len(consolidated["statements"]) == 2
    assert (
        consolidated["statements"][0]["evidence"][0]["segment_ids"]
        == statements[0]["segment_ids"]
    )


def test_invalid_provider_saved_no_precise_output(
    controlled_settings, tmp_path, monkeypatch
):
    from src.tools_knowledge import cs50_extraction_provider as providers

    original = providers.OpenAIHTTPProvider

    def handle(request):
        data = json.loads(json.loads(request.content)["messages"][1]["content"])
        cid = data["chunk_id"]
        raw = {
            "analysis": {"chunk_id": cid, "relevant": True},
            "extraction": {
                "chunk_id": cid,
                "statements": [
                    {
                        "statement_id": "bad",
                        "text": "candidate",
                        "semantic_type": "statement",
                        "segment_ids": [999999],
                    }
                ],
            },
        }
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"content": json.dumps(raw)}}
                ]
            },
        )

    monkeypatch.setattr(
        providers,
        "OpenAIHTTPProvider",
        lambda **kw: original(**kw, transport=httpx.MockTransport(handle)),
    )
    monkeypatch.setenv("CS50_KNOWLEDGE_EXECUTE_LLM", "1")
    config = {
        "execute_llm": True,
        "provider": "openai_http",
        "model": "fake",
        "probe_marvin": False,
        "plan": str(PLAN),
        "manifest": str(MANIFEST),
        "workspace": str(ROOT),
        "max_chunks": 1,
        "chunk_index": 20,
        "evidence_mode": "segment_v1",
        "token_budget": 60000,
        "input_limit": 28000,
        "output_limit": 1200,
    }
    cli.save(tmp_path / "configuration.json", config)
    assert cli.worker(tmp_path / "configuration.json") == 1
    assert (tmp_path / "chunk_0020.provider.json").exists()
    assert not (tmp_path / "extraction.json").exists()
    assert (
        json.loads((tmp_path / "quality_report.json").read_text())["evidence_scopes"][
            -1
        ]["scope"]
        == "invalid"
    )


def test_foreign_item_chunk():
    segments, chunk, raw = fixture()
    raw["extraction"]["statements"][0]["chunk_id"] = "foreign"
    with pytest.raises(EvidenceValidationError):
        bind_precise_candidates(raw, chunk, segments)


def test_whisper_and_legacy_binding_unchanged():
    from src.model_knowledge.data_knowledge import ChunkKnowledgeResult
    from src.tools_knowledge.find_knowledge import attach_chunk_provenance

    segments, chunk, raw = fixture()
    for item in raw["extraction"]["statements"] + raw["extraction"]["formulas"]:
        item.update(start=999, end=1000)
    result = attach_chunk_provenance(ChunkKnowledgeResult.model_validate(raw), chunk)
    assert all(
        item.segment_ids == chunk.segment_ids and item.start == chunk.start
        for item in result.extraction.statements + result.extraction.formulas
    )


def test_formula_missing_references_rejected():
    segments, chunk, raw = fixture()
    raw["extraction"]["formulas"][0].pop("segment_ids")
    with pytest.raises(EvidenceValidationError):
        bind_precise_candidates(raw, chunk, segments)
