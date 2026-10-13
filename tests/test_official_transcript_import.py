"""Synthetic local-only contract tests, with inference/network access forbidden."""

import __future__

import ast
import json
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.model_knowledge.data_knowledge import TranscriptChunk
from src.model_transcribe.data_transcribe import TranscriptDocument, TranscriptSegment
from src.tools_transcribe.import_transcript import (
    import_srt,
    import_transcript,
    import_txt,
    import_vtt,
    save_imported_transcript,
)

METADATA = {
    "language": "en",
    "original_url": "https://cs50.harvard.edu/test/transcript.txt",
}
SRT = "1\n00:00:01,250 --> 00:00:03,500\nHello &amp; welcome.\nSecond line.\n\n2\n00:00:03,000 --> 00:00:04,750\nHello &amp; welcome.\nSecond line.\n"
VTT = "WEBVTT\nKind: captions\n\nNOTE comment\nignored\n\nSTYLE\n::cue { color: white; }\n\nREGION\nid:main\n\nfirst\n00:01.250 --> 00:03.500 align:start\n<v David><b>Hello &amp; welcome.</b>\nSecond line.\n\n00:03.000 --> 00:04.750\nHello &amp; welcome.\nSecond line.\n"


@pytest.fixture(autouse=True)
def block_external_calls(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("External calls forbidden")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def source(tmp_path, kind, text):
    path = tmp_path / f"source.{kind}"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "kind,content,loader", [("srt", SRT, import_srt), ("vtt", VTT, import_vtt)]
)
def test_subtitle_order_times_multiline_and_repetition(tmp_path, kind, content, loader):
    path = source(tmp_path, kind, content)
    transcript = loader(path, **METADATA)
    assert [(seg.seg_id, seg.start, seg.end) for seg in transcript.segments] == [
        (0, 1.25, 3.5),
        (1, 3.0, 4.75),
    ]
    assert transcript.segments[0].text == "Hello & welcome.\nSecond line."
    assert transcript.segments[0].text == transcript.segments[1].text
    assert transcript.duration == 4.75
    assert transcript.provenance.transcript_source.value == "official_subtitle"
    assert transcript.provenance.source_url == METADATA["original_url"]
    assert transcript.provenance.media_format == kind
    assert transcript.provenance.transcription_provider is None
    assert transcript.runtime is None
    assert (
        TranscriptDocument.model_validate_json(transcript.model_dump_json())
        == transcript
    )
    assert list(tmp_path.iterdir()) == [path]  # import itself writes nothing


def test_txt_unknown_timestamps_paragraphs_and_unicode(tmp_path):
    path = source(
        tmp_path,
        "txt",
        "\ufeffCafé — Einführung.\r\nSecond line.\r\n\r\nCafé — Einführung.\r\n",
    )
    transcript = import_txt(path, **METADATA)
    assert [seg.seg_id for seg in transcript.segments] == [0, 1]
    assert transcript.segments[0].text == "Café — Einführung.\nSecond line."
    assert all(seg.start is None and seg.end is None for seg in transcript.segments)
    assert transcript.duration is None
    assert transcript.provenance.transcript_source.value == "official_transcript"
    assert transcript.provenance.language == transcript.language == "en"
    assert transcript.provenance.source_file == str(path)
    assert (
        TranscriptDocument.model_validate_json(transcript.model_dump_json())
        == transcript
    )


@pytest.mark.parametrize("encoding", ["cp1252", "utf-16"])
def test_explicit_encoding(tmp_path, encoding):
    path = tmp_path / "source.txt"
    path.write_bytes("Café — Einführung".encode(encoding))
    assert import_txt(path, encoding=encoding, **METADATA).text == "Café — Einführung"


def test_invalid_utf8_is_not_silently_replaced(tmp_path):
    path = tmp_path / "source.txt"
    path.write_bytes(b"\xff invalid")
    with pytest.raises(UnicodeDecodeError):
        import_txt(path, **METADATA)


@pytest.mark.parametrize("kind", ["txt", "srt", "vtt"])
@pytest.mark.parametrize("content", ["", " \n\t\n", "\ufeff"])
def test_empty_files_fail(tmp_path, kind, content):
    with pytest.raises(ValueError, match="Empty transcript"):
        import_transcript(source(tmp_path, kind, content), **METADATA)


@pytest.mark.parametrize(
    "timing",
    [
        "00:00:bogus --> 00:00:02,000",
        "00:60:00,000 --> 01:00:00,000",
        "00:00:02,000 --> 00:00:01,000",
        "-00:00:01,000 --> 00:00:02,000",
        "00:00:01,00 --> 00:00:02,000",
        "00:00:01.000 --> 00:00:02.000",
        "00:00:01,000 -> 00:00:02,000",
        "00:00:01,000 --> 00:00:02,000 garbage",
    ],
)
def test_corrupt_srt_timestamp_fails_whole_import(tmp_path, timing):
    with pytest.raises(ValueError, match="cue"):
        import_srt(
            source(tmp_path, "srt", SRT + f"\n3\n{timing}\nCorrupt\n"), **METADATA
        )


@pytest.mark.parametrize(
    "content",
    [
        "WEBVTT\n\n00:01,000 --> 00:02,000\nText",
        "WEBVTT\n\n00:99.000 --> 01:00.000\nText",
        "WEBVTT\n00:01.000 --> 00:02.000\nText",
        "00:01.000 --> 00:02.000\nText",
        "WEBVTT\n\nmissing timing\nText",
        "WEBVTT\n\nNOTE only comment",
        "WEBVTT\n\n00:01.000 --> 00:02.000\n<b></b>",
    ],
)
def test_corrupt_or_cueless_vtt(tmp_path, content):
    with pytest.raises(ValueError):
        import_vtt(source(tmp_path, "vtt", content), **METADATA)


def test_existing_model_timed_documents_still_validate():
    segment = TranscriptSegment(seg_id=0, start=0.0, end=3.0, text="Existing")
    transcript = TranscriptDocument(
        source="audio.mp3", segments=[segment], text="Existing"
    )
    assert (
        TranscriptDocument.model_validate_json(transcript.model_dump_json())
        == transcript
    )


def test_exclusive_save_and_no_overwrite(tmp_path):
    transcript = import_txt(source(tmp_path, "txt", "Text"), **METADATA)
    destination = tmp_path / "normalized.json"
    save_imported_transcript(transcript, destination)
    original = destination.read_bytes()
    assert TranscriptDocument.model_validate(json.loads(original)) == transcript
    with pytest.raises(FileExistsError):
        save_imported_transcript(transcript, destination)
    assert destination.read_bytes() == original
    link = tmp_path / "link.json"
    link.symlink_to(destination)
    with pytest.raises(FileExistsError):
        save_imported_transcript(transcript, link)
    assert destination.read_bytes() == original
    with pytest.raises(ValueError, match=".json"):
        save_imported_transcript(transcript, tmp_path / "invalid.txt")


def test_metadata_format_and_missing_file(tmp_path):
    path = source(tmp_path, "txt", "Text")
    with pytest.raises(ValueError):
        import_txt(path, language=" ", original_url=METADATA["original_url"])
    with pytest.raises(ValueError):
        import_txt(path, language="en", original_url="not a URL")
    with pytest.raises(FileNotFoundError):
        import_txt(tmp_path / "missing.txt", **METADATA)
    with pytest.raises(ValueError, match="Unsupported"):
        import_transcript(source(tmp_path, "csv", "Text"), **METADATA)


def test_knowledge_chunking_contract_without_llm_imports(tmp_path):
    # Execute the actual production function in isolation from Marvin/config/provider imports.
    path = Path(__file__).resolve().parents[1] / "src/tools_knowledge/find_knowledge.py"
    module = ast.parse(path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "build_transcript_chunks"
    )
    isolated = ast.Module(body=[function], type_ignores=[])
    namespace = {"TranscriptChunk": TranscriptChunk}
    exec(
        compile(
            isolated, str(path), "exec", flags=__future__.annotations.compiler_flag
        ),
        namespace,
    )
    chunker = namespace["build_transcript_chunks"]
    config = SimpleNamespace(target_duration=45, overlap_segments=2)
    timed = import_srt(source(tmp_path, "srt", SRT), **METADATA)
    chunks = chunker(config, timed)
    assert len(chunks) == 1
    assert chunks[0].segment_ids == [0, 1]
    assert (chunks[0].start, chunks[0].end) == (1.25, 4.75)
    with pytest.raises(ValueError, match="text-based chunking"):
        chunker(config, import_txt(source(tmp_path, "txt", "Timeless"), **METADATA))


def test_import_does_not_load_whisper_or_application_settings(tmp_path):
    import sys

    import_txt(source(tmp_path, "txt", "Text"), **METADATA)
    assert "faster_whisper" not in sys.modules
    assert "src.core.config" not in sys.modules
    assert "src.model_transcribe.provider_transcript" not in sys.modules


@pytest.mark.parametrize(
    "kind,content",
    [
        (
            "srt",
            "\ufeff17\r\n01:02:03,004 --> 01:02:05,006\r\nÉcole\r\n\r\n3\r\n01:02:04,000 --> 01:02:06,000\r\nAgain\r\n",
        ),
        (
            "vtt",
            "\ufeffWEBVTT\r\n\r\n17\r\n01:02:03.004 --> 01:02:05.006\r\nÉcole\r\n\r\n3\r\n01:02:04.000 --> 01:02:06.000\r\nAgain\r\n",
        ),
    ],
)
def test_bom_crlf_hours_and_source_cue_order(tmp_path, kind, content):
    document = import_transcript(source(tmp_path, kind, content), **METADATA)
    assert [segment.seg_id for segment in document.segments] == [0, 1]
    assert document.segments[0].start == pytest.approx(3723.004)
    assert document.segments[0].end == pytest.approx(3725.006)
    assert document.segments[0].text == "École"
