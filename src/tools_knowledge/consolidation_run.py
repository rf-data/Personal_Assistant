"""Offline consolidation audit and immutable write-ahead receipts (POSIX)."""

import fcntl
import hashlib
import json
import os
from collections import Counter
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Literal

from pydantic import Field

from src.model_knowledge.data_knowledge import (
    ConsolidatedKnowledgeDocument,
    LectureKnowledgeDocument,
    TranscriptKnowledgeDocument,
)
from src.tools_knowledge.consolidate_knowledge import consolidate_knowledge
from src.tools_knowledge.consolidation_validation import (
    Finding,
    exact_text,
    input_findings,
    validate_output,
)
from src.tools_knowledge.cs50_checkpoint import (
    Contract,
    atomic_json,
    encoded,
    fingerprint,
)
from src.tools_lecture.execute_cs50 import safe_path
from src.utils.text_helper import text_similarity

Status = Literal["pending", "completed", "skipped", "failed", "invalid", "stale"]


class RunConfig(Contract):
    schema_version: Literal[1] = 1
    algorithm: Literal["conservative_exact_v1"] = "conservative_exact_v1"
    stage: Literal["deterministic", "semantic"] = "deterministic"
    model_name: str = "offline"
    # Must identify the complete external stage contract (prompts/schema/settings).
    semantic_contract: str | None = None


class Receipt(Contract):
    schema_version: Literal[1] = 1
    phase: Literal["prepared", "completed"]
    input_path: str
    output_path: str
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    course_id: str
    lecture_id: str
    source_id: str


class InputResult(Contract):
    input_path: str
    output_path: str | None = None
    course_id: str | None = None
    lecture_id: str | None = None
    source_id: str | None = None
    selected: bool = True
    status: Status = "pending"
    decision: str = "not_examined"
    input_sha256: str | None = None
    output_sha256: str | None = None
    objects_processed: int = 0
    objects_remaining: int = 0
    objects_merged: int = 0
    duplicates: int = 0
    findings: tuple[Finding, ...] = ()


class RunReport(Contract):
    schema_version: Literal[1] = 1
    config: RunConfig
    write: bool
    inputs: tuple[InputResult, ...]
    counts: dict[str, int]
    report_sha256: str


def report_for(results, config, write):
    counts = dict(Counter(item.status for item in results))
    for status in ("pending", "completed", "skipped", "failed", "invalid", "stale"):
        counts.setdefault(status, 0)
    counts.update(
        lectures_examined=len(
            {(i.course_id, i.lecture_id) for i in results if i.lecture_id}
        ),
        inputs_examined=len(results),
        inputs_selected=sum(i.selected for i in results),
        objects_processed=sum(i.objects_processed for i in results),
        objects_remaining=sum(i.objects_remaining for i in results),
        objects_merged=sum(i.objects_merged for i in results),
        duplicates=sum(i.duplicates for i in results),
        conflicts=sum("conflict" in f.code for i in results for f in i.findings),
        missing_evidence_references=sum(
            f.code == "missing_evidence_reference" for i in results for f in i.findings
        ),
        warnings=sum(f.severity == "warning" for i in results for f in i.findings),
        errors=sum(f.severity == "error" for i in results for f in i.findings),
    )
    value = dict(
        schema_version=1,
        config=config.model_dump(mode="json"),
        write=write,
        inputs=[i.model_dump(mode="json") for i in results],
        counts=counts,
    )
    return RunReport(**value, report_sha256=fingerprint(value))


def hash_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path=None, *, raw=None):
    # Reject duplicate keys and NaN rather than accepting ambiguous JSON receipts.
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"Duplicate JSON key: {key}")
            value[key] = item
        return value

    def reject_number(value):
        raise ValueError(f"Invalid JSON number: {value}")

    return json.loads(
        path.read_bytes() if raw is None else raw,
        object_pairs_hook=unique,
        parse_constant=reject_number,
    )


def inspect_input(path, root, config):
    path = safe_path(root, path)
    raw = path.read_bytes()
    value = read_json(raw=raw)
    provenance = value.get("transcript_provenance") if isinstance(value, dict) else None
    if isinstance(provenance, dict) and not provenance.get("acquired_at"):
        raise ValueError(
            "Provenance acquired_at must be explicit for deterministic replay"
        )
    document = TranscriptKnowledgeDocument.model_validate(value)
    if not path.name.endswith("_know_extract.json"):
        raise ValueError("Input name must end in _know_extract.json")
    return document, hash_bytes(raw)


def conflict_findings(document, consolidated):
    """Report candidates for review; never assert semantic contradiction."""
    findings = []
    statements = consolidated.statements
    for idx, left in enumerate(statements):
        for right in statements[idx + 1 :]:
            if text_similarity(exact_text(left.text), exact_text(right.text)) >= 0.8:
                findings.append(
                    Finding(
                        code="possible_statement_conflict",
                        severity="warning",
                        message=f"Review distinct statements {left.statement_id}/{right.statement_id}; no semantic decision or merge",
                        chunk_id=right.evidence[0].chunk_id,
                        item_id=right.evidence[0].item_id,
                    )
                )
    for idx, left in enumerate(consolidated.formulas):
        for right in consolidated.formulas[idx + 1 :]:
            if text_similarity(left.plain_text, right.plain_text) >= 0.8:
                findings.append(
                    Finding(
                        code="possible_formula_conflict",
                        severity="warning",
                        message=f"Review distinct formulas {left.expression_id}/{right.expression_id}; no equivalence decision or merge",
                        chunk_id=right.evidence[0].chunk_id,
                        item_id=right.evidence[0].item_id,
                    )
                )
    for item in consolidated.formulas:
        evidence_ids = {(e.chunk_id, e.item_id) for e in item.evidence}
        statuses = {
            f.verification_status
            for c in document.chunks
            if c.extraction
            for f in c.extraction.formulas
            if (c.extraction.chunk_id, f.expression_id) in evidence_ids
        }
        if {"verified", "rejected"} <= statuses:
            findings.append(
                Finding(
                    code="verification_conflict",
                    severity="warning",
                    message=f"{item.expression_id}: verified and rejected evidence retained; status pending",
                    chunk_id=item.evidence[0].chunk_id,
                    item_id=item.evidence[0].item_id,
                )
            )
    return findings


def make_result(document, *, model_name="offline", semantic_stage=None):
    consolidated = consolidate_knowledge(document)
    result = (
        consolidated
        if semantic_stage is None
        else semantic_stage(document=consolidated, model_name=model_name)
    )
    expected = (
        ConsolidatedKnowledgeDocument
        if semantic_stage is None
        else LectureKnowledgeDocument
    )
    if not isinstance(result, expected):
        raise ValueError(f"Stage must return {expected.__name__}")
    validate_output(document, result)
    return consolidated, result


@contextmanager
def publication_lock(root):
    root = Path(root).absolute()
    safe_path(root, root / ".consolidation.lock")
    root.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        root / ".consolidation.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


def process_one(entry, document, output_root, config, *, write, semantic_stage):
    suffix = (
        "_know_deterministic.json"
        if config.stage == "deterministic"
        else "_know_consol.json"
    )
    filename = Path(entry.input_path).name.removesuffix("_know_extract.json") + suffix
    output = safe_path(output_root, Path(output_root) / filename)
    prepared_path = safe_path(
        output_root, output.with_name(output.name + ".prepared.v1.json")
    )
    done_path = safe_path(
        output_root, output.with_name(output.name + ".completed.v1.json")
    )
    updates = dict(output_path=str(output))
    try:
        receipt = None
        if prepared_path.exists():
            receipt = Receipt.model_validate(read_json(prepared_path))
            if receipt.phase != "prepared":
                raise ValueError("Invalid prepared receipt phase")
            identity = dict(
                input_path=entry.input_path,
                output_path=str(output),
                input_sha256=entry.input_sha256,
                config_sha256=fingerprint(config.model_dump(mode="json")),
                course_id=document.course_id,
                lecture_id=document.lecture_id,
                source_id=document.source_id,
            )
            if any(getattr(receipt, key) != value for key, value in identity.items()):
                return entry.model_copy(
                    update={
                        **updates,
                        "status": "stale",
                        "decision": "input_or_configuration_changed",
                        "findings": (
                            *entry.findings,
                            Finding(
                                code="stale_receipt",
                                severity="error",
                                message="Receipt identity differs; choose a new output root",
                            ),
                        ),
                    }
                )
        if done_path.exists():
            done = Receipt.model_validate(read_json(done_path))
            if receipt is None or done != receipt.model_copy(
                update={"phase": "completed"}
            ):
                raise ValueError("Completion marker conflicts with prepared receipt")
            if not output.exists():
                raise ValueError("Completed output is missing")
        if output.exists():
            # Parse old schemas too: no migration/adoption even when they validate.
            cls = (
                ConsolidatedKnowledgeDocument
                if config.stage == "deterministic"
                else LectureKnowledgeDocument
            )
            existing = cls.model_validate(read_json(output))
            validate_output(document, existing)
            if receipt is None:
                raise ValueError(
                    "Unreceipted output; valid schema alone cannot authorize reuse"
                )
            if hash_bytes(output.read_bytes()) != receipt.output_sha256:
                raise ValueError("Output hash differs from prepared receipt")
            result = existing
            consolidated = consolidate_knowledge(document)
        else:
            if receipt is None and done_path.exists():
                raise ValueError("Orphan completion marker")
            if not write and config.stage == "semantic":
                return entry.model_copy(
                    update={
                        **updates,
                        "status": "pending",
                        "decision": "semantic_stage_requires_explicit_execution",
                    }
                )
            consolidated, result = make_result(
                document, model_name=config.model_name, semantic_stage=semantic_stage
            )
            expected_hash = hash_bytes(encoded(result.model_dump(mode="json")))
            if receipt and receipt.output_sha256 != expected_hash:
                raise ValueError("Interrupted stage cannot reproduce prepared output")
        value = result.model_dump(mode="json")
        output_hash = hash_bytes(encoded(value))
        # Hash references always describe actual bytes when output already exists.
        if output.exists():
            output_hash = hash_bytes(output.read_bytes())
        raw_count = consolidated.stats.statements_raw + consolidated.stats.formulas_raw
        remaining = len(consolidated.statements) + len(consolidated.formulas)
        updates.update(
            output_sha256=output_hash,
            objects_processed=raw_count,
            objects_remaining=len(result.statements) + len(result.formulas),
            objects_merged=raw_count - remaining,
            duplicates=raw_count - remaining,
            findings=(*entry.findings, *conflict_findings(document, consolidated)),
        )
        if hash_bytes(Path(entry.input_path).read_bytes()) != entry.input_sha256:
            raise ValueError(
                "Input changed during consolidation; no publication allowed"
            )
        if done_path.exists():
            updates.update(status="skipped", decision="verified_completed")
        elif not write:
            updates.update(
                status="pending",
                decision="resume_prepared" if receipt else "validated_dry_run",
            )
        else:
            if receipt is None:
                receipt = Receipt(
                    phase="prepared",
                    input_path=entry.input_path,
                    output_path=str(output),
                    input_sha256=entry.input_sha256,
                    config_sha256=fingerprint(config.model_dump(mode="json")),
                    output_sha256=output_hash,
                    course_id=document.course_id,
                    lecture_id=document.lecture_id,
                    source_id=document.source_id,
                )
                atomic_json(prepared_path, receipt.model_dump(mode="json"))
            if not output.exists():
                atomic_json(output, value)
            atomic_json(
                done_path,
                receipt.model_copy(update={"phase": "completed"}).model_dump(
                    mode="json"
                ),
            )
            updates.update(status="completed", decision="published_or_resumed")
    except (OSError, ValueError) as error:
        updates.update(
            status="invalid",
            decision="validation_or_publication_conflict",
            findings=(
                *entry.findings,
                Finding(code="invalid_artifact", severity="error", message=str(error)),
            ),
        )
    except Exception as error:
        updates.update(
            status="failed",
            decision="stage_failed",
            findings=(
                *entry.findings,
                Finding(
                    code="stage_failed",
                    severity="error",
                    message=f"{type(error).__name__}: {error}",
                ),
            ),
        )
    return entry.model_copy(update=updates)


def run_course(
    input_paths,
    output_root,
    *,
    input_root,
    config=None,
    write=False,
    course_id=None,
    lecture_ids=(),
    semantic_stage=None,
):
    config = config or RunConfig()
    if (config.stage == "semantic") != (semantic_stage is not None) or (
        config.stage == "semantic" and not (config.semantic_contract or "").strip()
    ):
        raise ValueError(
            "Semantic stage requires an explicit callable and versioned semantic_contract"
        )
    roots = Path(input_root).absolute(), Path(output_root).absolute()
    # Validate paths before creating any output directory or lock file.
    safe_path(roots[1], roots[1] / ".consolidation.lock")
    paths = sorted({Path(p).absolute() for p in input_paths})
    loaded, entries = {}, []
    for path in paths:
        entry = InputResult(input_path=str(path))
        try:
            document, digest = inspect_input(path, roots[0], config)
            entry = entry.model_copy(
                update=dict(
                    course_id=document.course_id,
                    lecture_id=document.lecture_id,
                    source_id=document.source_id,
                    input_sha256=digest,
                )
            )
            if (course_id and document.course_id != course_id) or (
                lecture_ids and document.lecture_id not in lecture_ids
            ):
                entry = entry.model_copy(
                    update=dict(
                        selected=False, status="skipped", decision="not_selected"
                    )
                )
            else:
                findings = input_findings(document, strict=True)
                entry = entry.model_copy(update=dict(findings=tuple(findings)))
                if any(f.severity == "error" for f in findings):
                    entry = entry.model_copy(
                        update=dict(status="invalid", decision="invalid_input")
                    )
                else:
                    loaded[str(path)] = document
        except (OSError, ValueError) as error:
            entry = entry.model_copy(
                update=dict(
                    status="invalid",
                    decision="unreadable_input",
                    findings=(
                        Finding(
                            code="invalid_input", severity="error", message=str(error)
                        ),
                    ),
                )
            )
        entries.append(entry)
    # Flattened historical naming must not mix sources, even on first publication.
    names = Counter(Path(e.input_path).name for e in entries if e.selected)
    identities = Counter(
        (e.course_id, e.lecture_id, e.source_id)
        for e in entries
        if e.selected and e.source_id
    )
    sources = Counter(e.source_id for e in entries if e.selected and e.source_id)
    for idx, entry in enumerate(entries):
        if entry.status == "pending" and (
            names[Path(entry.input_path).name] > 1
            or identities[(entry.course_id, entry.lecture_id, entry.source_id)] > 1
            or sources[entry.source_id] > 1
        ):
            entries[idx] = entry.model_copy(
                update=dict(
                    status="invalid",
                    decision="identity_or_filename_collision",
                    findings=(
                        *entry.findings,
                        Finding(
                            code="identity_conflict",
                            severity="error",
                            message="Duplicate source identity or flattened output name; inputs remain separate",
                        ),
                    ),
                )
            )
    with publication_lock(roots[1]) if write else nullcontext():
        for idx, entry in enumerate(entries):
            if entry.status == "pending":
                try:
                    entries[idx] = process_one(
                        entry,
                        loaded[entry.input_path],
                        roots[1],
                        config,
                        write=write,
                        semantic_stage=semantic_stage,
                    )
                except (OSError, ValueError) as error:
                    entries[idx] = entry.model_copy(
                        update=dict(
                            status="invalid",
                            decision="unsafe_output_path",
                            findings=(
                                *entry.findings,
                                Finding(
                                    code="invalid_path",
                                    severity="error",
                                    message=str(error),
                                ),
                            ),
                        )
                    )
    return report_for(entries, config, write)
