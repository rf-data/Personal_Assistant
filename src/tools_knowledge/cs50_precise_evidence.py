"""Candidate cue references; authoritative times come only from original segments."""

import copy

from src.model_knowledge.data_knowledge import (
    ChunkAnalysis,
    ChunkKnowledgeResult,
    KnowledgeExtract,
    KnowledgeStatement,
    MathExpression,
)

INPUT_VERSION = "cs50_segment_evidence_v1"


class EvidenceValidationError(ValueError):
    def __init__(self, reason, audit):
        super().__init__(reason)
        self.audit = audit


def bind_precise_candidates(payload, chunk, segments, audit=None):
    audit = audit if audit is not None else []
    value = copy.deepcopy(payload)

    def fail(reason, item_id=None, kind=None):
        audit.append(
            {
                "chunk_id": chunk.chunk_id,
                "item_id": item_id,
                "kind": kind,
                "scope": "invalid",
                "reason": reason,
            }
        )
        raise EvidenceValidationError(reason, audit)

    forbidden = {
        "source_id",
        "course_id",
        "lecture_id",
        "resource_id",
        "transcript_url",
        "transcript_provenance",
        "media_id",
    }
    if not isinstance(value, dict):
        fail("Malformed result payload")
    if set(value) - set(ChunkKnowledgeResult.model_fields):
        fail("Provider must not supply source identity or unknown result fields")
    if not isinstance(value.get("analysis"), dict) or set(value["analysis"]) - set(
        ChunkAnalysis.model_fields
    ):
        fail("Unknown analysis identity or fields")
    if forbidden.intersection(value):
        fail("Provider must not supply source identity")
    if value.get("analysis", {}).get("chunk_id") != chunk.chunk_id:
        fail("Foreign analysis chunk identity")
    extraction = value.get("extraction")
    if extraction is None:
        return ChunkKnowledgeResult.model_validate(value)
    if not isinstance(extraction, dict) or set(extraction) - set(
        KnowledgeExtract.model_fields
    ):
        fail("Unknown extraction identity or fields")
    if extraction.get("chunk_id") != chunk.chunk_id:
        fail("Foreign extraction chunk identity")
    if forbidden.intersection(extraction):
        fail("Provider must not supply source identity")
    for field in ("statements", "formulas"):
        if not isinstance(extraction.get(field, []), list):
            fail("Malformed evidence item list", kind=field)
    for kind, field, id_field in [
        ("statement", "statements", "statement_id"),
        ("formula", "formulas", "expression_id"),
    ]:
        seen = set()
        for item in extraction.get(field, []):
            model = KnowledgeStatement if kind == "statement" else MathExpression
            if not isinstance(item, dict) or set(item) - set(model.model_fields):
                fail("Foreign item identity or unknown fields", kind=kind)
            item_id = item.get(id_field)
            if item_id in seen:
                fail("Duplicate item identity", item_id, kind)
            seen.add(item_id)
            if (
                forbidden.intersection(item)
                or item.get("source", "transcript") != "transcript"
            ):
                fail("Foreign source reference", item_id, kind)
            ids = item.get("segment_ids")
            if not isinstance(ids, list) or not ids:
                fail("Missing segment references", item_id, kind)
            if any(type(i) is not int for i in ids) or len(set(ids)) != len(ids):
                fail("Duplicate or non-integer segment references", item_id, kind)
            if any(
                i not in chunk.segment_ids
                or i not in segments
                or not segments[i].text.strip()
                for i in ids
            ):
                fail("Unknown, empty or foreign-chunk segment", item_id, kind)
            # Preserve actual source order; never accept model-generated times.
            ids = [i for i in chunk.segment_ids if i in ids]
            selected = [segments[i] for i in ids]
            try:
                for segment in selected:
                    segment.require_timestamps()
            except ValueError as exc:
                fail(str(exc), item_id, kind)
            item.update(
                segment_ids=ids,
                start=min(s.start for s in selected),
                end=max(s.end for s in selected),
                source="transcript",
            )
            audit.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "item_id": item_id,
                    "kind": kind,
                    "scope": "statement_precise",
                    "segment_ids": ids,
                    "start": item["start"],
                    "end": item["end"],
                }
            )
    try:
        return ChunkKnowledgeResult.model_validate(value)
    except ValueError:
        fail("Invalid result schema")


def precise_input(chunk, segments):
    for i in chunk.segment_ids:
        segments[i].require_timestamps()
    return {
        "input_version": INPUT_VERSION,
        "chunk_id": chunk.chunk_id,
        "target_chunk": chunk.text,
        "previous_context": chunk.previous_context,
        "next_context": chunk.next_context,
        "segments": [
            {
                "seg_id": i,
                "start": segments[i].start,
                "end": segments[i].end,
                "text": segments[i].text,
            }
            for i in chunk.segment_ids
        ],
        "instruction": "For each statement and formula return only supporting segment_ids from these segments. "
        "Do not return timestamps, source identities or source modality. Return the supplied chunk_id. "
        "Every item needs nonempty supporting IDs. These are unverified candidates, not proof of entailment.",
    }
