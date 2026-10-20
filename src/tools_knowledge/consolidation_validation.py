"""Conservative identity/evidence checks shared by consolidation and its runner."""

import math
import re
import unicodedata
from typing import Literal

from src.tools_knowledge.cs50_checkpoint import Contract, fingerprint


class Finding(Contract):
    code: str
    severity: Literal["error", "warning"]
    message: str
    chunk_id: str | None = None
    item_id: str | None = None


def exact_text(text):
    """Keep case, punctuation, operators and superscripts significant."""
    return unicodedata.normalize("NFC", text).strip()


def exact_math(text):
    # Only ordinary ASCII spaces around explicit punctuation are insignificant.
    # Never join two identifiers or a TeX control word and its following letter.
    text = exact_text(text)
    if "\\" in text:
        return text
    return re.sub(r" *([+\-=^_{}()/]) *", r"\1", text)


def input_findings(document, *, strict=False):
    findings = []

    def add(code, message, chunk=None, item=None, severity="error"):
        findings.append(
            Finding(
                code=code,
                severity=severity,
                message=message,
                chunk_id=chunk,
                item_id=item,
            )
        )

    for field in ("source_id", "course_id", "lecture_id"):
        if not (getattr(document, field) or "").strip():
            add(
                "missing_identity",
                field,
                severity="error" if strict or field == "source_id" else "warning",
            )
    if document.transcript_provenance is None:
        add(
            "missing_provenance",
            "No transcript acquisition provenance; nothing inferred",
            severity="warning",
        )
    elif not (
        document.transcript_provenance.source_url
        or document.transcript_provenance.source_file
    ):
        add(
            "missing_provenance",
            "Provenance has no source URL/file",
            severity="warning",
        )
    chunks, identities = {}, {}
    for chunk in document.chunks:
        cid = chunk.analysis.chunk_id
        if not cid.strip():
            add("missing_evidence_reference", "Blank chunk ID", cid)
        value = fingerprint(chunk.model_dump(mode="json"))
        if cid in chunks and chunks[cid] != value:
            add("identity_conflict", "Different chunks share an identity", cid)
        chunks[cid] = value
        extraction = chunk.extraction
        if extraction is None:
            if chunk.analysis.relevant:
                add(
                    "missing_extraction",
                    "Relevant chunk has no extraction",
                    cid,
                    severity="error" if strict else "warning",
                )
            continue
        if extraction.chunk_id != cid:
            add(
                "missing_evidence_reference",
                "Analysis/extraction chunk IDs differ",
                cid,
            )
        for kind, items in (
            ("statement", extraction.statements),
            ("formula", extraction.formulas),
        ):
            for item in items:
                iid = item.statement_id if kind == "statement" else item.expression_id
                key = (cid, kind, iid)
                payload = fingerprint(item.model_dump(mode="json"))
                if key in identities and identities[key] != payload:
                    add(
                        "identity_conflict",
                        "Different objects share a chunk/item identity",
                        cid,
                        iid,
                    )
                identities[key] = payload
                if not iid.strip() or not item.segment_ids:
                    add(
                        "missing_evidence_reference",
                        "Missing item ID or segment references",
                        cid,
                        iid,
                        severity="error" if strict else "warning",
                    )
                if any(seg < 0 for seg in item.segment_ids):
                    add(
                        "missing_evidence_reference",
                        "Negative segment reference",
                        cid,
                        iid,
                    )
                if not (
                    math.isfinite(item.start)
                    and math.isfinite(item.end)
                    and 0 <= item.start <= item.end
                ):
                    add(
                        "invalid_evidence_range",
                        "Non-finite, negative or reversed time interval",
                        cid,
                        iid,
                    )
                text = item.text if kind == "statement" else item.plain_text
                if not text.strip():
                    add(
                        "empty_object",
                        "Blank content would be silently omitted",
                        cid,
                        iid,
                    )
                if item.llm_confidence is not None and not (
                    0 <= item.llm_confidence <= 1
                ):
                    add(
                        "invalid_confidence",
                        "Confidence must be finite and in [0,1]",
                        cid,
                        iid,
                    )
        if extraction.entities or extraction.relations or extraction.summary:
            add(
                "unprojected_fields",
                "Deterministic output does not project extraction entities/relations/summary",
                cid,
                severity="warning",
            )
    for candidate in document.visual_candidates:
        if candidate.chunk_id not in chunks:
            add(
                "missing_evidence_reference",
                "Visual candidate refers to an unknown chunk",
                candidate.chunk_id,
            )
        if not candidate.segment_ids:
            add(
                "missing_evidence_reference",
                "Visual candidate has no segment references",
                candidate.chunk_id,
                severity="error" if strict else "warning",
            )
        if not (
            math.isfinite(candidate.start)
            and math.isfinite(candidate.end)
            and 0 <= candidate.start <= candidate.end
        ):
            add(
                "invalid_evidence_range",
                "Invalid visual candidate interval",
                candidate.chunk_id,
            )
    return findings


def require_valid(document, *, strict=False):
    findings = input_findings(document, strict=strict)
    errors = [f for f in findings if f.severity == "error"]
    if errors:
        raise ValueError(
            "; ".join(f"{f.code}:{f.chunk_id}:{f.item_id}: {f.message}" for f in errors)
        )
    return findings


def validate_output(document, result):
    """Check metadata and complete, unmodified evidence including discarded items."""
    from src.model_knowledge.data_knowledge import LectureKnowledgeDocument
    from src.tools_knowledge.consolidate_knowledge import (
        build_formula_evidence,
        build_statement_evidence,
        consolidate_knowledge,
    )

    for field in (
        "source_id",
        "course_id",
        "lecture_id",
        "language",
        "media_id",
        "transcript_url",
        "transcript_provenance",
        "visual_candidates",
    ):
        if getattr(result, field) != getattr(document, field):
            raise ValueError(f"Output changed source metadata: {field}")
    expected = {"statement": set(), "formula": set()}
    for chunk in document.chunks:
        if not chunk.analysis.relevant or chunk.extraction is None:
            continue
        for kind, items, build in (
            ("statement", chunk.extraction.statements, build_statement_evidence),
            ("formula", chunk.extraction.formulas, build_formula_evidence),
        ):
            expected[kind].update(
                fingerprint(
                    build(chunk.analysis.chunk_id, item).model_dump(mode="json")
                )
                for item in items
            )
    for kind, items in (("statement", result.statements), ("formula", result.formulas)):
        ids = [
            item.statement_id if kind == "statement" else item.expression_id
            for item in items
        ]
        if any(not item.strip() for item in ids) or len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate/blank output {kind} IDs")
        if any(
            not (item.text if kind == "statement" else item.plain_text).strip()
            for item in items
        ):
            raise ValueError(f"Blank output {kind} content")
        if any(not item.evidence for item in items):
            raise ValueError(f"Output {kind} has no evidence")
        evidence = [e for item in items for e in item.evidence]
        if kind == "statement" and isinstance(result, LectureKnowledgeDocument):
            evidence.extend(
                e for item in result.discarded_statements for e in item.evidence
            )
        signatures = [fingerprint(e.model_dump(mode="json")) for e in evidence]
        if len(signatures) != len(set(signatures)):
            raise ValueError(f"Output counted {kind} evidence more than once")
        actual = set(signatures)
        if actual != expected[kind]:
            raise ValueError(f"Output lost, changed or invented {kind} evidence")

    baseline = consolidate_knowledge(document)
    if isinstance(result, LectureKnowledgeDocument):
        allowed = {s.statement_id for s in baseline.statements}
        assignments = [sid for s in result.statements for sid in s.source_statement_ids]
        assignments.extend(s.source_statement_id for s in result.discarded_statements)
        if set(assignments) != allowed or len(assignments) != len(set(assignments)):
            raise ValueError(
                "Semantic source IDs must cover each deterministic statement once"
            )
        mapping = {s.statement_id: s for s in baseline.statements}
        for statement in result.statements:
            expected_evidence = {
                fingerprint(e.model_dump(mode="json"))
                for sid in statement.source_statement_ids
                for e in mapping[sid].evidence
            }
            if {
                fingerprint(e.model_dump(mode="json")) for e in statement.evidence
            } != expected_evidence:
                raise ValueError(
                    "Semantic statement evidence contradicts its source IDs"
                )
        for discarded in result.discarded_statements:
            if discarded.evidence != mapping[discarded.source_statement_id].evidence:
                raise ValueError(
                    "Discarded statement evidence contradicts its source ID"
                )
        final_ids = {s.statement_id for s in result.statements}
        if any(
            not set(entity.source_statement_ids) <= final_ids
            for entity in result.entities
        ):
            raise ValueError("Entity references unknown canonical statement IDs")
        if result.formulas != baseline.formulas:
            raise ValueError("Semantic stage changed preserved formulas")
    elif result != baseline:
        raise ValueError("Output does not match deterministic consolidation")
