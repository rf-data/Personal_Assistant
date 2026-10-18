"""Unknown-time boundaries using real models, source bytes and production adapters."""

import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from content_adapter_support import attest, dump, srt
from pydantic import ValidationError

from src.content_store.adapters import verify_srt_bundle
from src.content_store.errors import UnverifiedBinding
from src.content_store.models import ContentLocator
from src.model_knowledge.data_knowledge import TranscriptChunk
from src.model_transcribe.data_transcribe import TranscriptDocument, TranscriptSegment
from src.tools_knowledge.cs50_precise_evidence import (
    EvidenceValidationError,
    bind_precise_candidates,
    precise_input,
)
from src.tools_lecture.adapt_cs50 import CS50AdapterPlan
from src.tools_lecture.execute_cs50 import (
    ExecutionConflict,
    validate_document,
    validate_order,
)
from src.tools_rag.cs50_embeddings import source_time_window
from src.tools_transcribe.import_transcript import import_txt, save_imported_transcript

ROOT = Path(__file__).resolve().parents[1]
METADATA = dict(language="en", original_url="https://example.invalid/official.txt")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline transcript contracts only")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.mark.parametrize("start,end", [(0, 0), (1.25, 4.5), (None, None)])
def test_interval_json_roundtrip(start, end):
    value = dict(seg_id=0, start=start, end=end, text="Café ∑")
    segment = TranscriptSegment.model_validate(value)
    assert json.loads(segment.model_dump_json()) == value | dict(
        speaker=None, confidence=None
    )
    assert TranscriptSegment.model_validate_json(segment.model_dump_json()) == segment
    if start is None:
        with pytest.raises(ValueError, match="unknown_transcript_time"):
            segment.require_timestamps()
    else:
        assert segment.require_timestamps() == (start, end)


@pytest.mark.parametrize(
    "start,end",
    [
        (None, 1),
        (0, None),
        (-1, 1),
        (0, -1),
        (2, 1),
        (float("inf"), 2),
        (0, float("inf")),
        (float("nan"), 1),
        (0, float("nan")),
        (float("-inf"), 0),
    ],
)
def test_invalid_intervals_rejected_in_models_and_json(start, end):
    value = dict(seg_id=0, start=start, end=end, text="Invalid")
    with pytest.raises(ValidationError):
        TranscriptSegment.model_validate(value)
    with pytest.raises(ValidationError):
        TranscriptSegment.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("missing", ["start", "end"])
def test_null_is_explicit_not_a_missing_field(missing):
    value = dict(seg_id=0, start=None, end=None, text="Text")
    del value[missing]
    with pytest.raises(ValidationError):
        TranscriptSegment.model_validate(value)


@pytest.mark.parametrize("start,end", [(None, 1), (2, 1), (0, float("inf"))])
def test_window_guards_copies_without_validation(start, end):
    original = TranscriptSegment(seg_id=0, start=0, end=1, text="Known")
    copied = original.model_copy(update=dict(start=start, end=end))
    with pytest.raises(ValueError, match="transcript_time"):
        source_time_window([copied])


def test_schema_requires_explicit_nullable_pair():
    schema = TranscriptSegment.model_json_schema()
    assert {"start", "end"}.issubset(schema["required"])
    for field in ("start", "end"):
        assert {part.get("type") for part in schema["properties"][field]["anyOf"]} == {
            "number",
            "null",
        }


def test_unknown_duration_and_mixed_document_guard():
    unknown = TranscriptSegment(seg_id=1, start=None, end=None, text="Unknown")
    timed = TranscriptSegment(seg_id=0, start=0, end=1, text="Known")
    document = TranscriptDocument(
        source="mixed.json", segments=[timed, unknown], text="Known Unknown"
    )
    assert document.duration is None
    with pytest.raises(ValueError, match="unknown_transcript_time"):
        document.require_timestamps()
    with pytest.raises(ValidationError, match="duration must be null"):
        TranscriptDocument.model_validate(document.model_dump() | dict(duration=1))
    assert (
        TranscriptDocument.model_validate_json(document.model_dump_json()) == document
    )


def test_old_numeric_json_retains_fields_and_values():
    # Legacy numeric documents need neither a schema version nor a new capability field.
    value = dict(
        source="old.mp3",
        segments=[dict(seg_id=3, start=0, end=4.25, text="Old")],
        text="Old",
        duration=4.25,
    )
    document = TranscriptDocument.model_validate_json(json.dumps(value))
    document.require_timestamps()
    assert document.segments[0].model_dump(exclude_none=True) == value["segments"][0]
    assert "time_status" not in document.model_dump_json()


def test_txt_preserves_text_provenance_raw_hash_and_repeats(tmp_path):
    raw = "\ufeff  Café — e\u0301 & <tag>\r\nSecond.\r\n\r\n\r\n \t\r\n  ∑ x²  \r\n".encode()
    source = tmp_path / "official.txt"
    source.write_bytes(raw)
    before = hashlib.sha256(raw).hexdigest()
    first, second = (import_txt(source, **METADATA) for _ in range(2))
    normalized = raw.decode("utf-8-sig").replace("\r\n", "\n")
    assert first.text == normalized
    assert [s.text for s in first.segments] == [
        "  Café — e\u0301 & <tag>\nSecond.",
        "  ∑ x²  \n",
    ]
    # Acquisition time describes each import event; every other field is reproducible.
    exclude = {"provenance": {"acquired_at"}}
    assert first.model_dump(exclude=exclude) == second.model_dump(exclude=exclude)
    output = tmp_path / "official.json"
    save_imported_transcript(first, output)
    loaded = TranscriptDocument.model_validate_json(output.read_bytes())
    assert loaded == first and loaded.text == normalized and loaded.duration is None
    assert loaded.provenance.source_file == loaded.source == str(source)
    assert loaded.provenance.source_url == METADATA["original_url"]
    assert loaded.provenance.language == loaded.language == "en"
    assert loaded.provenance.media_format == "txt"
    assert loaded.provenance.transcript_source.value == "official_transcript"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before


def test_binary_nul_is_rejected_without_encoding_guess(tmp_path):
    source = tmp_path / "source.txt"
    source.write_bytes(b"T\x00e\x00x\x00t\x00")
    with pytest.raises(ValueError, match="NUL"):
        import_txt(source, **METADATA)


def test_timed_evidence_and_retrieval_reject_unknown():
    segment = TranscriptSegment(seg_id=0, start=None, end=None, text="Timeless")
    chunk = TranscriptChunk(
        chunk_id="chunk_0000",
        segment_ids=[0],
        start=0,
        end=1,
        text=segment.text,
        n_words=1,
    )
    payload = dict(
        analysis=dict(chunk_id=chunk.chunk_id, relevant=True),
        extraction=dict(
            chunk_id=chunk.chunk_id,
            statements=[
                dict(
                    statement_id="S1",
                    text="Claim",
                    semantic_type="statement",
                    segment_ids=[0],
                )
            ],
        ),
    )
    with pytest.raises(
        EvidenceValidationError, match="unknown_transcript_time"
    ) as error:
        bind_precise_candidates(payload, chunk, {0: segment})
    assert error.value.audit[-1]["scope"] == "invalid"
    with pytest.raises(ValueError, match="unknown_transcript_time"):
        precise_input(chunk, {0: segment})
    with pytest.raises(ValueError, match="unknown_transcript_time"):
        source_time_window([segment])
    with pytest.raises(ValueError, match="No original cues"):
        source_time_window([])
    known = TranscriptSegment(seg_id=1, start=1.25, end=7.5, text="Known")
    assert source_time_window([known]) == (1.25, 7.5)
    with pytest.raises(ValueError, match="unknown_transcript_time"):
        source_time_window([known, segment])


def test_unknown_locator_compatible_but_not_srt_binding(tmp_path):
    bundle, document = srt(tmp_path)
    plan = CS50AdapterPlan.model_validate_json(bundle.plan_path.read_bytes())
    binding = next(
        b for c in plan.courses for b in c.bindings if b.source_id == bundle.source_id
    )
    raw_before = bundle.raw_path.read_bytes()
    value = document.model_dump(mode="json")
    value["segments"][0].update(start=None, end=None)
    value["duration"] = None
    unknown = TranscriptDocument.model_validate(value)
    locator = ContentLocator(
        raw_artifact_sha256=hashlib.sha256(raw_before).hexdigest(),
        origin_pointer="/segments/0",
        original_segment_id=0,
        time_status="unknown",
        start=None,
        end=None,
    )
    assert ContentLocator.model_validate_json(locator.model_dump_json()) == locator
    assert locator.start is None and locator.end is None
    with pytest.raises(ValueError, match="unknown_transcript_time"):
        validate_order(unknown)
    dump(bundle.transcript_path, value)
    with pytest.raises(ExecutionConflict, match="unknown_transcript_time"):
        validate_document(bundle.transcript_path, binding, bundle.raw_path)
    # Even a receipt/implementation hash update cannot turn null times into checked SRT.
    receipt = json.loads(bundle.receipt_path.read_bytes())
    for action in receipt["actions"].values():
        if action["action"] == "parse_subtitle":
            action["sha256"] = hashlib.sha256(
                bundle.transcript_path.read_bytes()
            ).hexdigest()
    dump(bundle.receipt_path, receipt)
    attest(bundle)
    with pytest.raises(UnverifiedBinding, match="unverified_binding"):
        verify_srt_bundle(bundle)
    assert bundle.raw_path.read_bytes() == raw_before


def test_fresh_import_has_no_application_initialization(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("Café", encoding="utf-8")
    code = """
import socket, sys
def forbidden(*args, **kwargs):
    raise AssertionError('No network')
socket.socket.connect = forbidden
socket.getaddrinfo = forbidden
from src.tools_transcribe.import_transcript import import_txt
assert import_txt(sys.argv[1], language='en', original_url='https://example.invalid/a.txt').duration is None
for name in ('faster_whisper', 'marvin', 'src.core.config', 'src.core.memory', 'src.model_transcribe.provider_transcript'):
    assert name not in sys.modules, name
"""
    subprocess.run(
        [sys.executable, "-c", code, str(source)],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=True,
        timeout=15,
    )
