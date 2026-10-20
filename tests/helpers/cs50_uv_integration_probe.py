"""Real imports and original local SRT; called in an isolated installed-uv subprocess."""

import hashlib
import importlib.metadata
import json
import logging
import os
import socket
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(root))
os.chdir(output)
os.environ.update(
    ROOT=str(output),
    CHROMA_DIR=str(output / "chroma"),
    DATA_DIR=str(output / "data"),
    WIKI_EN_API="https://example.invalid",
    HEADER_AGENT="offline-integration",
    HF_API_KEY="offline-placeholder",
    OPENAI_API_KEY="offline-placeholder",
)
network_attempts = []


def forbidden(*args, **kwargs):
    network_attempts.append("blocked")
    raise AssertionError("No network permitted")


socket.socket.connect = forbidden
socket.socket.connect_ex = forbidden
socket.getaddrinfo = forbidden
socket.create_connection = forbidden


def main():
    # Full normal imports: no AST, sys.modules substitutes or helper injection.
    from src.core.memory import app_session

    app_session.logger = logging.getLogger("cs50-offline-integration")
    app_session.logger.addHandler(logging.NullHandler())
    from src.core.config_knowledge import KnowledgeSettings
    from src.model_discovery.cs50 import ResourceRole
    from src.model_knowledge.data_knowledge import (
        ChunkKnowledgeResult,
        TranscriptKnowledgeDocument,
    )
    from src.model_transcribe.data_transcribe import TranscriptDocument
    from src.tools_knowledge import consolidate_knowledge as consolidation_module
    from src.tools_knowledge.consolidate_knowledge import consolidate_knowledge
    from src.tools_knowledge.find_knowledge import (
        attach_chunk_provenance,
        build_transcript_chunks,
        enrich_chunks,
        validate_extraction,
    )
    from src.tools_lecture.prepare_cs50 import discover_fixture_courses
    from src.tools_transcribe.import_transcript import (
        import_srt,
        save_imported_transcript,
    )
    from src.utils.dict_helper import load_dict, save_dict
    from src.utils.latex_helper import normalize_math_text

    assert consolidation_module.normalize_math_text is normalize_math_text
    paths = list((root / "docs/course_sources/cs50").rglob("*.html"))
    paths.append(root / "docs/course_sources/cs50/manifest.json")
    courses = discover_fixture_courses(paths[-1])
    course = next(item for item in courses if item.course_id == "cs50_python")
    subtitle = next(
        item
        for item in course.resources
        if item.role == ResourceRole.SUBTITLES and item.section_keys == ("0",)
    )
    lecture = next(
        item
        for item in course.resources
        if item.role == ResourceRole.LECTURE_VIDEO and item.section_keys == ("0",)
    )
    source = root / "data/lectures/cs50_python/lecture0.srt.txt"
    synthetic = not source.exists()
    if synthetic:
        source = output / "cs50_python_week0.synthetic.srt"
        source.write_text(
            "1\n00:00:00,000 --> 00:00:30,000\nSynthetic fixture.\n\n2\n00:00:30,000 --> 00:01:00,000\nSynthetic fixture.\n\n3\n00:01:00,000 --> 00:01:30,000\nSynthetic fixture.\n",
            encoding="utf-8",
        )
    paths.append(source)
    before = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths
    }
    strict_error = None
    try:
        transcript = import_srt(
            source, language=subtitle.language, original_url=str(subtitle.original_url)
        )
    except ValueError as error:
        strict_error = str(error)
        assert "empty cue text" in strict_error
        transcript = import_srt(
            source,
            language=subtitle.language,
            original_url=str(subtitle.original_url),
            preserve_empty_cues=True,
        )
    transcript_path = output / f"{source.name}.json"
    save_imported_transcript(transcript, transcript_path)
    loaded = load_dict(transcript_path, cls=TranscriptDocument)
    assert loaded == transcript
    chunks = build_transcript_chunks(
        KnowledgeSettings(target_duration=45, overlap_segments=2), loaded
    )
    enrich_chunks(chunks)
    assert len(chunks) >= 2
    results = []
    for index, chunk in enumerate(chunks):
        result = ChunkKnowledgeResult.model_validate(
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
                            "statement_id": f"S{index}",
                            "text": "Synthetic integration statement (not an extracted claim).",
                            "semantic_type": "statement",
                            "segment_ids": [],
                            "start": 0,
                            "end": 0,
                        }
                    ],
                    "formulas": [
                        {
                            "expression_id": f"F{index}",
                            "plain_text": "a + b",
                            "latex": "a+b",
                            "expression_type": "calculation",
                            "segment_ids": [],
                            "start": 0,
                            "end": 0,
                        }
                    ],
                },
            }
        )
        attach_chunk_provenance(result, chunk)
        validate_extraction(result)
        results.append(result)
    media_ids = {variant.media_id for variant in lecture.variants if variant.media_id}
    media_id = next(iter(media_ids)) if len(media_ids) == 1 else None
    document = TranscriptKnowledgeDocument(
        source_id=transcript_path.name.removesuffix(".json"),
        transcript_url=loaded.provenance.source_url,
        language=loaded.language,
        transcript_provenance=loaded.provenance,
        course_id=course.course_id,
        lecture_id=lecture.resource_id,
        media_id=media_id,
        chunks=results,
        visual_candidates=[],
    )
    extraction_path = output / "pilot_knowledge.json"
    save_dict(document.model_dump(mode="json"), extraction_path, mode="x")
    restored = load_dict(extraction_path, cls=TranscriptKnowledgeDocument)
    assert restored == document
    consolidated = consolidate_knowledge(restored)
    assert consolidated.source_id == document.source_id
    assert consolidated.transcript_url == document.transcript_url
    assert consolidated.transcript_metadata() == document.transcript_metadata()
    assert consolidated.media_id == document.media_id
    evidence_report = []
    for item in [*consolidated.statements, *consolidated.formulas]:
        assert len(item.evidence) == len(chunks)
        for evidence, chunk in zip(item.evidence, chunks, strict=True):
            assert (
                evidence.chunk_id,
                evidence.segment_ids,
                evidence.start,
                evidence.end,
            ) == (chunk.chunk_id, chunk.segment_ids, chunk.start, chunk.end)
            assert evidence.source == "transcript"
            evidence_report.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "segment_ids": chunk.segment_ids,
                    "start": chunk.start,
                    "end": chunk.end,
                }
            )
    assert before == {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths
    }
    assert not network_attempts
    assert "faster_whisper" not in sys.modules
    assert "marvin" not in sys.modules
    assert not list(output.rglob("*.db"))
    report = {
        "python": sys.executable,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["pydantic", "pytest", "marvin", "tiktoken"]
        },
        "source": str(source),
        "synthetic_source": synthetic,
        "sha256": before[str(source)],
        "strict_import_error": strict_error,
        "segments": len(loaded.segments),
        "empty_segments": [
            segment.seg_id for segment in loaded.segments if not segment.text
        ],
        "duration": loaded.duration,
        "chunks": len(chunks),
        "source_id": consolidated.source_id,
        "transcript_url": consolidated.transcript_url,
        "language": consolidated.language,
        "course_id": consolidated.course_id,
        "lecture_id": consolidated.lecture_id,
        "media_id": consolidated.media_id,
        "provenance": consolidated.transcript_provenance.model_dump(mode="json"),
        "evidence": evidence_report,
        "network_attempts": len(network_attempts),
        "steps": {
            name: "passed"
            for name in [
                "discovery",
                "srt_import",
                "transcript_json",
                "real_chunking_import",
                "chunking",
                "synthetic_evidence_binding",
                "knowledge_json",
                "real_consolidation_import",
                "formula_helper",
                "consolidation",
                "metadata",
                "source_unchanged",
            ]
        },
    }
    (output / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


main()
