"""Deterministic diagnostic proxies; no relevance judging or automatic filtering."""

import re
from collections import Counter

from src.model_knowledge.data_knowledge import TranscriptKnowledgeDocument

QUALITY_VERSION = "cs50_quality_v1"
LOW_VALUE_CUES = (
    (
        "speaker_or_course_intro",
        re.compile(r"\b(my name is|this is cs50|our week on)\b", re.I),
    ),
    (
        "audience_assumption",
        re.compile(r"\b(many of you|most of you|odds are)\b", re.I),
    ),
    ("transition", re.compile(r"\b(let'?s start|let me go ahead)\b", re.I)),
    ("vague_popularity", re.compile(r"\b(very popular|nowadays)\b", re.I)),
)


def quality_report(document, chunks, *, worker_report=None):
    document = TranscriptKnowledgeDocument.model_validate(document.model_dump())
    by_id = {chunk.chunk_id: chunk for chunk in chunks}
    if len(by_id) != len(chunks):
        raise ValueError("Duplicate chunk IDs in quality input")
    statements, formulas, findings = [], [], []
    irrelevant = 0
    coarse = 0
    signatures = []
    mismatched = 0
    for result in document.chunks:
        chunk_id = result.analysis.chunk_id
        if chunk_id not in by_id:
            raise ValueError("Unknown result chunk in quality input")
        chunk = by_id[chunk_id]
        if result.extraction is None:
            continue
        items = result.extraction.statements + result.extraction.formulas
        if not result.analysis.relevant:
            irrelevant += len(result.extraction.statements)
        statements.extend(result.extraction.statements)
        formulas.extend(result.extraction.formulas)
        for item in items:
            full = (
                item.segment_ids == chunk.segment_ids
                and item.start == chunk.start
                and item.end == chunk.end
            )
            coarse += full
            signatures.append((chunk_id, tuple(item.segment_ids), item.start, item.end))
            invalid = (
                not item.segment_ids
                or not set(item.segment_ids).issubset(chunk.segment_ids)
                or item.start < chunk.start
                or item.end > chunk.end
                or item.start > item.end
            )
            mismatched += invalid
        for statement in result.extraction.statements:
            reasons = [
                name
                for name, pattern in LOW_VALUE_CUES
                if pattern.search(statement.text)
            ]
            if reasons:
                findings.append(
                    {
                        "chunk_id": chunk_id,
                        "statement_id": statement.statement_id,
                        "reasons": reasons,
                    }
                )
    normalized = Counter(
        re.sub(r"\s+", " ", s.text.strip().casefold()) for s in statements
    )
    evidence_count = len(signatures)
    validation = "not_available"
    if worker_report is not None and worker_report.get("result_origin") == "synthetic":
        validation = "not_llm_synthetic"
    elif worker_report is not None and worker_report.get("result_origin") == "LLM":
        validation = (
            "reported_valid"
            if worker_report.get("validated") is True
            else "reported_not_valid"
        )
    return {
        "quality_version": QUALITY_VERSION,
        "source_id": document.source_id,
        "course_id": document.course_id,
        "lecture_id": document.lecture_id,
        "chunk_ids": [r.analysis.chunk_id for r in document.chunks],
        "metrics": {
            "statements": len(statements),
            "formulas": len(formulas),
            "statements_in_irrelevant_chunks": irrelevant,
            "low_learning_value_proxy_count": len(findings),
            "missing_statement_topics": sum(
                not s.topic or not s.topic.strip() for s in statements
            ),
            "exact_duplicate_statement_excess": sum(n - 1 for n in normalized.values()),
            "evidence_items": evidence_count,
            "full_chunk_evidence_items": coarse,
            "full_chunk_evidence_ratio": coarse / evidence_count
            if evidence_count
            else None,
            "distinct_evidence_signatures": len(set(signatures)),
            "invalid_evidence_references": mismatched,
        },
        "low_learning_value_proxies": findings,
        "validation": {"pydantic_document": True, "llm_worker_status": validation},
        "limits": [
            "Proxy rules are not gold labels or confirmed irrelevance",
            "Pydantic validation does not establish factual grounding",
            "Post-bound evidence cannot recover original LLM evidence",
            "Evidence range checks do not prove statement-level entailment",
        ],
    }
