"""Diagnostic metrics and real concept-chunk selection without gold claims or APIs."""

import json
from pathlib import Path

import pytest
from test_cs50_knowledge_pilot import (  # genuine Settings/socket fixture reused
    MANIFEST,
    PLAN,
    ROOT,
)
from test_cs50_knowledge_pilot import controlled_settings as controlled_settings

from scripts import cs50_knowledge_pilot as cli
from src.model_knowledge.data_knowledge import (
    ChunkKnowledgeResult,
    TranscriptChunk,
    TranscriptKnowledgeDocument,
)
from src.tools_knowledge.cs50_quality import quality_report


def test_metrics_are_proxies_not_gold_labels():
    chunk = TranscriptChunk(
        chunk_id="c",
        segment_ids=[1, 2],
        start=1,
        end=4,
        text="Local fixture",
        n_words=2,
    )
    result = ChunkKnowledgeResult.model_validate(
        {
            "analysis": {"chunk_id": "c", "relevant": False},
            "extraction": {
                "chunk_id": "c",
                "statements": [
                    {
                        "statement_id": str(i),
                        "text": "My name is Example",
                        "semantic_type": "statement",
                        "segment_ids": [1, 2],
                        "start": 1,
                        "end": 4,
                        "topic": None,
                    }
                    for i in range(2)
                ],
                "formulas": [],
            },
        }
    )
    document = TranscriptKnowledgeDocument(
        source_id="test",
        transcript_url=None,
        media_id=None,
        chunks=[result],
        visual_candidates=[],
    )
    report = quality_report(document, [chunk])
    metrics = report["metrics"]
    assert metrics["statements_in_irrelevant_chunks"] == 2
    assert metrics["missing_statement_topics"] == 2
    assert metrics["exact_duplicate_statement_excess"] == 1
    assert metrics["low_learning_value_proxy_count"] == 2
    assert metrics["full_chunk_evidence_ratio"] == 1
    assert metrics["distinct_evidence_signatures"] == 1
    assert report["validation"]["llm_worker_status"] == "not_available"
    assert document.chunks[0].extraction.statements[0].text == "My name is Example"


def test_no_evidence_ratio_not_invented():
    document = TranscriptKnowledgeDocument(
        source_id="test",
        transcript_url=None,
        media_id=None,
        chunks=[],
        visual_candidates=[],
    )
    assert quality_report(document, [])["metrics"]["full_chunk_evidence_ratio"] is None


@pytest.mark.parametrize(
    "index,count", [(20, 1), (20, 2), (156, 1), (156, 2), (157, 1)]
)
def test_offline_index_selection(
    controlled_settings, tmp_path, monkeypatch, index, count
):
    monkeypatch.chdir(ROOT)
    output = tmp_path / "run"
    code = cli.main(
        [
            "--plan",
            str(PLAN),
            "--manifest",
            str(MANIFEST),
            "--output",
            str(output),
            "--chunk-index",
            str(index),
            "--max-chunks",
            str(count),
        ]
    )
    report = json.loads((output / "worker_result.json").read_text())
    assert report["requests"] == 0
    if index + count > 157:
        assert code == 1 and not (output / "chunks.json").exists()
    else:
        assert code == 0
        chunk = json.loads((output / "chunks.json").read_text())[0]
        assert chunk["chunk_id"] == f"chunk_{index:04d}"
        assert (output / "quality_report.json").exists()
        assert len(json.loads((output / "chunks.json").read_text())) == count
        assert (
            json.loads((output / "quality_report.json").read_text())["validation"][
                "llm_worker_status"
            ]
            == "not_llm_synthetic"
        )
        if index == 20:
            assert "input function" in chunk["text"] and "argument" in chunk["text"]
            assert chunk["start"] == 792.44 and chunk["end"] == 837.44


def test_negative_index_before_output(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(
            [
                "--plan",
                str(PLAN),
                "--manifest",
                str(MANIFEST),
                "--output",
                str(tmp_path / "run"),
                "--chunk-index",
                "-1",
            ]
        )
    assert not (tmp_path / "run").exists()


def test_capture_before_overwrite_on_real_concept_fixture(
    controlled_settings, tmp_path, monkeypatch
):
    from src.model_transcribe.data_transcribe import TranscriptDocument
    from src.tools_knowledge import cs50_extraction_provider as providers

    manifest = json.loads(MANIFEST.read_text())["inputs"][0]
    transcript = TranscriptDocument.model_validate_json(
        Path(manifest["transcript_json_path"]).read_bytes()
    )
    by_id = {s.seg_id: s for s in transcript.segments}

    class FakeProvider:
        def __init__(self, **kwargs):
            self.budget = kwargs["budget"]

        def extract(self, chunk, record):
            assert chunk.chunk_id == "chunk_0020"
            ids = chunk.segment_ids[:3]
            quotation = "\n".join(by_id[i].text for i in ids)
            return ChunkKnowledgeResult.model_validate(
                {
                    "analysis": {"chunk_id": chunk.chunk_id, "relevant": True},
                    "extraction": {
                        "chunk_id": chunk.chunk_id,
                        "statements": [
                            {
                                "statement_id": "quote",
                                "text": quotation,
                                "semantic_type": "statement",
                                "segment_ids": ids,
                                "start": by_id[ids[0]].start,
                                "end": by_id[ids[-1]].end,
                                "topic": "input function",
                            }
                        ],
                        "formulas": [],
                    },
                }
            )

        def close(self):
            pass

    monkeypatch.setattr(providers, "OpenAIHTTPProvider", FakeProvider)
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
        "token_budget": 60000,
        "input_limit": 28000,
        "output_limit": 1200,
    }
    cli.save(tmp_path / "configuration.json", config)
    assert cli.worker(tmp_path / "configuration.json") == 0
    original = json.loads((tmp_path / "chunk_0020.provider.json").read_text())[
        "extraction"
    ]["statements"][0]
    bound = json.loads((tmp_path / "extraction.json").read_text())["chunks"][0][
        "extraction"
    ]["statements"][0]
    assert len(original["segment_ids"]) == 3 and len(bound["segment_ids"]) > 3
    assert (
        original["text"] == bound["text"]
    )  # verbatim actual source, no invented gold assertion
    assert original["end"] < bound["end"]
    assert (
        json.loads((tmp_path / "quality_report.json").read_text())["metrics"][
            "full_chunk_evidence_items"
        ]
        == 1
    )
