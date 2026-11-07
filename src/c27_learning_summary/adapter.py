"""Read-only adapters. Never acquire, parse, execute or discover files implicitly."""

from pathlib import Path

from src.c27_learning_summary.export_policy import metadata_text
from src.c27_learning_summary.models import (
    Catalog,
    ProcessingArtifact,
    SourceProvenance,
    SourceRef,
)
from src.content_store.models import ContentBlock, ContentLocator, fingerprint
from src.model_transcribe.data_transcribe import TranscriptDocument

MAX_CATALOG_BYTES = 8 * 1024 * 1024


def load_catalog(path: Path) -> Catalog:
    with path.open("rb") as stream:
        data = stream.read(MAX_CATALOG_BYTES + 1)
    if len(data) > MAX_CATALOG_BYTES:
        raise ValueError("Catalog byte limit exceeded")
    try:
        return Catalog.model_validate_json(data)
    except ValueError:
        raise ValueError("Catalog validation failed") from None


def artifact(blocks, *, artifact_id, parser_version, last_run):
    return ProcessingArtifact(
        artifact_id=artifact_id,
        parser_version=parser_version,
        last_run=last_run,
        payload_sha256=fingerprint([b.model_dump(mode="json") for b in blocks]),
    )


def transcript_blocks(document: TranscriptDocument, *, raw_sha256: str):
    """Caller supplies independently reviewed original hash; no invented timestamps."""
    ids = [s.seg_id for s in document.segments]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate transcript segment IDs")
    return tuple(
        ContentBlock(
            block_id=f"cue:{s.seg_id}",
            order=i,
            type="paragraph",
            original_type="transcript_segment",
            payload_pointer=f"/segments/{i}",
            text=s.text,
            locators=(
                ContentLocator(
                    raw_artifact_sha256=raw_sha256,
                    origin_pointer=f"/segments/{i}",
                    original_segment_id=s.seg_id,
                    time_status="known" if s.start is not None else "unknown",
                    start=s.start,
                    end=s.end,
                ),
            ),
        )
        for i, s in enumerate(document.segments)
    )


def material_handoff_blocks(review):
    """Consume existing prepare_material_handoff result, including its quality gate."""
    if not review.report.passed or review.handoff is None:
        raise ValueError("Existing material quality gate failed")
    doc = review.handoff.document
    active = {u.block.block_id for u in review.handoff.aggregation_units}
    return tuple(
        ContentBlock(
            block_id=b.block_id,
            order=b.order,
            type="formula" if b.type == "math" else b.type,
            original_type=b.type,
            payload_pointer=f"/blocks/{i}",
            text=b.text,
            data=b.data,
            aggregation_role="primary" if b.block_id in active else "structure",
            locators=(
                ContentLocator(
                    raw_artifact_sha256=doc.raw_sha256,
                    origin_pointer=f"/blocks/{i}",
                    time_status="not_applicable",
                    **b.location.model_dump(),
                ),
            ),
        )
        for i, b in enumerate(doc.blocks)
    )


def validate_input(catalog, course_id, week_id, lecture_id, selected):
    # Round trip catches mutations in inherited legacy models or nested dicts.
    catalog = Catalog.model_validate_json(catalog.model_dump_json())
    try:
        course = next(c for c in catalog.courses if c.course_id == course_id)
        week = next(w for w in course.weeks if w.section_id == week_id)
        unit = next(u for u in week.units if u.section_id == lecture_id)
    except StopIteration:
        raise ValueError("Course/week/lecture scope absent from catalog") from None
    ids = {m.material_id for m in unit.materials}
    if not selected or len(set(selected)) != len(selected) or not set(selected) <= ids:
        raise ValueError("Explicit unique source selection within the lecture required")
    warnings = []
    materials = []
    for m in unit.materials:
        if not m.available or m.processing_status != "completed":
            warnings.append(
                f"Material {m.material_id}: {m.processing_status}; missing evidence"
            )
        if m.material_id not in selected:
            continue
        if (
            not m.available
            or m.processing_status != "completed"
            or m.verification == "unverified"
            or not m.artifact
        ):
            raise ValueError(
                f"Selected material is unavailable/unverified/unprocessed: {metadata_text(m.material_id)}"
            )
        if not any(
            b.text.strip() and b.aggregation_role == "primary" for b in m.blocks
        ):
            raise ValueError(
                f"Selected material has no primary text: {metadata_text(m.material_id)}"
            )
        if m.verification == "synthetic_test_only":
            warnings.append(f"Material {m.material_id}: synthetic_test_only")
        materials.append(m)
    return catalog, course, week, unit, tuple(materials), warnings


def source_slices(course_id, week_id, lecture_id, materials, config):
    refs = []
    for material in sorted(materials, key=lambda m: m.material_id):
        for block in sorted(material.blocks, key=lambda b: b.order):
            if block.aggregation_role != "primary" or not block.text.strip():
                continue
            for offset in range(0, len(block.text), config.chunk_chars):
                text = block.text[offset : offset + config.chunk_chars]
                if not text.strip():
                    continue
                data = dict(
                    course_id=course_id,
                    week_id=week_id,
                    lecture_id=lecture_id,
                    material_id=material.material_id,
                    source_id=material.source_id,
                    source_path=material.source_path,
                    provenance=SourceProvenance(
                        source_url=material.resource.source_url,
                        license=material.resource.license,
                        attribution=material.attribution,
                        title=material.resource.title,
                    ).model_dump(mode="json"),
                    content_hash=material.resource.content_hash,
                    parser_version=material.artifact.parser_version,
                    artifact_id=material.artifact.artifact_id,
                    block_id=block.block_id,
                    offset_start=offset,
                    offset_end=offset + len(text),
                    locators=[loc.model_dump(mode="json") for loc in block.locators],
                    text=text,
                )
                refs.append(SourceRef(ref_id=fingerprint(data), **data))
                if len(refs) > config.max_chunks:
                    raise ValueError(
                        "Chunk limit exceeded; narrow source selection or increase chunk size"
                    )
    return tuple(refs)
