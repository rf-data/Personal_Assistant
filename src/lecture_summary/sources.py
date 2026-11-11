"""Bounded source collection. No discovery downloads, parsers or inference jobs."""

import json

from src.content_store.models import ContentLocator, fingerprint, sha256
from src.lecture_summary.models import Evidence
from src.model_materials.materials import NormalizedDocument
from src.model_transcribe.data_transcribe import TranscriptDocument

MAX_INPUT_BYTES = 26000  # Conservative UTF-8 token upper bound; fail, never truncate.
MAX_BLOCKS = 160
MAX_FILE_BYTES = 2 * 1024 * 1024


def resolve(catalog, selection):
    catalog = type(catalog).model_validate_json(catalog.model_dump_json())
    selection = type(selection).model_validate_json(selection.model_dump_json())
    lectures = {
        v.lecture_id: v
        for v in catalog.lectures
        if (v.provider_id, v.course_id) == (selection.provider_id, selection.course_id)
    }
    if any(key not in lectures for key in selection.lecture_ids):
        raise ValueError("Unknown course/lecture ID in explicit selection")
    chosen = tuple(lectures[key] for key in selection.lecture_ids)
    if any(not v.sources for v in chosen):
        raise ValueError("Selected lecture has no registered sources")
    return chosen


def source_blocks(artifact, raw):
    """Preserve native locators; unknown video times remain explicitly unknown."""
    sha = artifact.sha256
    if artifact.format in {"txt", "md"}:
        text = raw.decode("utf-8-sig")
        if "\x00" in text:
            raise ValueError("Invalid source text encoding")
        lines = text.splitlines(keepends=True)
        current, start = "", 1
        for no, line in enumerate(lines, 1):
            if len(line) > 6000:
                raise ValueError("Source line exceeds supported chunk size")
            if len(current) + len(line) > 5000:
                yield (
                    current,
                    ContentLocator(
                        raw_artifact_sha256=sha,
                        origin_pointer="/",
                        line_start=start,
                        line_end=no - 1,
                        time_status="not_applicable",
                    ),
                    (),
                )
                current, start = "", no
            current += line
        if current.strip():
            yield (
                current,
                ContentLocator(
                    raw_artifact_sha256=sha,
                    origin_pointer="/",
                    line_start=start,
                    line_end=len(lines),
                    time_status="not_applicable",
                ),
                (),
            )
    elif artifact.format == "transcript_json":
        doc = TranscriptDocument.model_validate_json(raw)
        ids = [s.seg_id for s in doc.segments]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate transcript segment ID")
        # Retain exact segments; reject oversized contexts without silent sampling.
        for i, segment in enumerate(doc.segments):
            if segment.text.strip():
                yield (
                    segment.text,
                    ContentLocator(
                        raw_artifact_sha256=sha,
                        origin_pointer=f"/segments/{i}",
                        original_segment_id=segment.seg_id,
                        time_status="known" if segment.start is not None else "unknown",
                        start=segment.start,
                        end=segment.end,
                    ),
                    ("transcript_requires_visual_check_for_math",),
                )
    elif artifact.format == "document_json":
        doc = NormalizedDocument.model_validate_json(raw)
        for i, block in enumerate(doc.blocks):
            if block.text.strip():
                location = block.location
                yield (
                    block.text,
                    ContentLocator(
                        raw_artifact_sha256=sha,
                        origin_pointer=f"/blocks/{i}",
                        page=location.page,
                        dom=location.dom,
                        line_start=location.line_start,
                        line_end=location.line_end,
                        bbox=location.bbox,
                        time_status="not_applicable",
                    ),
                    tuple(block.uncertainty),
                )
    else:
        # Knowledge extracts are already LLM-derived: never silently assert originals.
        from src.model_knowledge.data_knowledge import TranscriptKnowledgeDocument

        doc = TranscriptKnowledgeDocument.model_validate_json(raw)
        for i, chunk in enumerate(doc.chunks):
            if chunk.extraction:
                for field in ("statements", "formulas"):
                    for j, item in enumerate(getattr(chunk.extraction, field)):
                        yield (
                            item.text if field == "statements" else item.plain_text,
                            ContentLocator(
                                raw_artifact_sha256=sha,
                                origin_pointer=f"/chunks/{i}/extraction/{field}/{j}",
                                time_status="unknown",
                            ),
                            ("derived_knowledge_not_independent_evidence",)
                            + (("derived_formula_requires_source_review",) if field == "formulas" else ()),
                        )


def collect(catalog, selection, storage):
    evidence, versions = [], []
    total = 0
    for lecture in resolve(catalog, selection):
        for artifact in lecture.sources:
            raw = storage.read(
                artifact.storage_id, artifact.relative_path, maximum=MAX_FILE_BYTES
            )
            if sha256(raw) != artifact.sha256:
                raise ValueError(
                    "Source version changed; explicitly register the new fingerprint"
                )
            metadata = {}
            if artifact.format.endswith("_json"):
                native = json.loads(raw)
                if not isinstance(native, dict):
                    raise ValueError("Structured source must be an object")
                for field, expected in (
                    ("provider_id", lecture.provider_id),
                    ("course_id", lecture.course_id),
                    ("lecture_id", lecture.lecture_id),
                ):
                    if native.get(field) is not None and native[field] != expected:
                        raise ValueError("Contradictory source course/lecture metadata")
                provenance = (
                    native.get("provenance")
                    or native.get("transcript_provenance")
                    or {}
                )
                if not isinstance(provenance, dict):
                    raise ValueError("Invalid structured source provenance")
                metadata = {
                    "native_source_id": native.get("source_id"),
                    "media_id": provenance.get("media_id") or native.get("media_id"),
                }
                if not artifact.source_url and provenance.get("source_url"):
                    metadata["source_url"] = provenance["source_url"]
                if artifact.format == "document_json":
                    document = NormalizedDocument.model_validate_json(raw)
                    if (
                        document.binding.resource.course_id != lecture.course_id
                        or document.binding.lecture_ids
                        and lecture.lecture_id not in document.binding.lecture_ids
                    ):
                        raise ValueError(
                            "Document binding contradicts selected lecture"
                        )
                    metadata.update(
                        native_source_id=document.binding.source_id,
                        native_document_id=document.document_id,
                        original_artifact_sha256=document.raw_sha256,
                    )
            versions.append(
                (
                    lecture.lecture_id,
                    artifact.artifact_id,
                    artifact.sha256,
                    artifact.format,
                    artifact.role,
                    artifact.title,
                    artifact.parent_artifact_ids,
                    artifact.source_url,
                )
            )
            document_id = fingerprint([artifact.artifact_id, artifact.sha256])
            source_url = metadata.pop("source_url", artifact.source_url)
            count = 0
            for text, locator, warnings in source_blocks(artifact, raw):
                if not text.strip():
                    continue
                count += 1
                chunk = fingerprint(
                    [document_id, locator.model_dump(mode="json"), text]
                )
                source_id = "evidence:" + fingerprint(
                    [lecture.provider_id, lecture.course_id, lecture.lecture_id, chunk]
                )
                item_metadata = {}
                if artifact.format == "knowledge_json":
                    parts = locator.origin_pointer.split("/")
                    native_chunk = native["chunks"][int(parts[2])]
                    item = native_chunk["extraction"][parts[4]][int(parts[5])]
                    item_metadata = dict(
                        native_chunk_id=native_chunk["analysis"]["chunk_id"],
                        native_item_id=item.get("statement_id") or item.get("expression_id"),
                        parent_segment_ids=tuple(item.get("segment_ids", [])),
                    )
                evidence.append(
                    Evidence(
                        source_id=source_id,
                        provider_id=lecture.provider_id,
                        course_id=lecture.course_id,
                        lecture_id=lecture.lecture_id,
                        artifact_id=artifact.artifact_id,
                        artifact_sha256=artifact.sha256,
                        artifact_role=artifact.role,
                        document_id=document_id,
                        chunk_id=chunk,
                        title=artifact.title,
                        text=text,
                        locator=locator,
                        warnings=warnings,
                        source_url=source_url,
                        parent_artifact_ids=artifact.parent_artifact_ids,
                        **metadata,
                        **item_metadata,
                    )
                )
                total += len(text.encode("utf-8"))
                if total > MAX_INPUT_BYTES or len(evidence) > MAX_BLOCKS:
                    raise ValueError(
                        "Input context limit exceeded; explicitly register a smaller source/lecture group"
                    )
            if not count:
                raise ValueError("Registered source contains no usable text")
    return tuple(evidence), tuple(sorted(versions))
