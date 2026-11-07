"""Bounded offline lecture orchestration over the existing M1 summary engine."""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field

from scripts import cs50_learning_mvp as mvp
from src import cs50_summary_mvp as m1
from src.c27_learning_summary.adapter import iter_source_slices
from src.c27_learning_summary.engine import generate_refs, messages_for
from src.c27_learning_summary.llm import FakeLLM
from src.c27_learning_summary.models import SourceRef, SummaryConfig, SummaryResult
from src.c27_learning_summary.store import SummaryStore
from src.content_store.artifacts import explicit_root
from src.content_store.models import canonical, fingerprint, sha256
from src.content_store.reader import private_bytes
from src.job_control.models import Contract, Sha
from src.runtime_paths import checked_path
from src.tools_lecture.execute_cs50 import write_state
from src.tools_materials.storage import publish_bytes

ADAPTER_VERSION = "one-source-summary-m2a-v1"
Hold = m1.Hold


class BatchLimits(Contract):
    total_slices: int = Field(default=512, ge=1, le=512)
    batches: int = Field(default=32, ge=1, le=32)
    requests: int = Field(default=512, ge=1, le=512)
    wall_seconds: float = Field(default=600, ge=1, le=600, allow_inf_nan=False)
    raw_output_bytes: int = Field(default=32_000_000, ge=1, le=64_000_000)
    stored_output_bytes: int = Field(default=128_000_000, ge=1, le=256_000_000)
    evidence_bytes: int = Field(default=16_000_000, ge=1, le=16_000_000)


class PlannedBatch(Contract):
    batch_id: Sha
    ordinal: int = Field(ge=0, le=31)
    refs: tuple[SourceRef, ...] = Field(min_length=1, max_length=32)
    request_sha256: tuple[Sha, ...] = Field(min_length=1, max_length=32)


class BatchPlan(Contract):
    schema_version: Literal[1] = 1
    source: dict[str, str]
    blocks_sha256: Sha
    config: SummaryConfig
    limits: BatchLimits
    batches: tuple[PlannedBatch, ...] = Field(min_length=1, max_length=32)
    total_slices: int = Field(ge=1, le=512)
    total_requests: int = Field(ge=1, le=512)
    eligible_chars: int = Field(ge=1)
    excluded_blocks: tuple[dict[str, str], ...]


class BatchApproval(m1.SummaryApproval):
    """An explicit operator input. Planning never creates an approved attestation."""

    schema_version: Literal[2]
    adapter_version: Literal["one-source-summary-m2a-v1"]
    limits: BatchLimits
    plan: BatchPlan


def request_bytes(ref, config):
    return json.dumps(messages_for(ref, config), ensure_ascii=False).encode()


def make_plan(identity, blocks, doc, config, limits):
    config = SummaryConfig.model_validate_json(config.model_dump_json())
    limits = BatchLimits.model_validate_json(limits.model_dump_json())
    if config.provider != "fake" or config.retries != 0:
        raise Hold("batch processing requires FakeLLM and zero retries")
    catalog, scope, _ = m1.catalog_for(identity, blocks, doc)
    materials = catalog.courses[0].weeks[0].units[0].materials
    refs = []
    for ref in iter_source_slices(*scope, materials, config, include_whitespace=True):
        refs.append(ref)
        if len(refs) > min(limits.total_slices, limits.requests):
            raise Hold("total slice/request limit exceeded; no truncation")
    if not refs:
        raise Hold("no eligible source text")
    # Independent reconstruction proves every original codepoint exactly once.
    cursor = 0
    for block in blocks:
        if block.aggregation_role != "primary" or not block.text.strip():
            continue
        start = 0
        while start < len(block.text):
            if cursor >= len(refs):
                raise Hold("missing source slice")
            ref = refs[cursor]
            end = min(start + config.chunk_chars, len(block.text))
            if (
                ref.block_id != block.block_id
                or ref.offset_start != start
                or ref.offset_end != end
                or ref.text != block.text[start:end]
                or ref.source_id != identity["source_id"]
                or ref.content_hash != identity["raw_sha256"]
                or ref.locators != block.locators
                or ref.ref_id
                != fingerprint(ref.model_dump(mode="json", exclude={"ref_id"}))
            ):
                raise Hold("original SourceRef/locator/coverage conflict")
            start, cursor = end, cursor + 1
    if cursor != len(refs) or len({r.ref_id for r in refs}) != len(refs):
        raise Hold("extra or duplicate source slices")
    requests = [request_bytes(r, config) for r in refs]
    if any(len(r) > config.max_input_bytes for r in requests):
        raise Hold("serialized request byte limit exceeded")
    # Reserve the engine's hard per-reply maximum before making any request.
    if len(refs) * 128000 > limits.raw_output_bytes:
        raise Hold("planned worst-case raw output exceeds total budget")
    batches = []
    for start in range(0, len(refs), config.max_chunks):
        data = dict(
            ordinal=len(batches),
            refs=refs[start : start + config.max_chunks],
            request_sha256=tuple(
                sha256(r) for r in requests[start : start + config.max_chunks]
            ),
        )
        if len(batches) >= limits.batches:
            raise Hold("total batch limit exceeded")
        batch_id = fingerprint(
            dict(
                source=identity,
                config=config.model_dump(mode="json"),
                limits=limits.model_dump(mode="json"),
                ordinal=data["ordinal"],
                refs=[r.model_dump(mode="json") for r in data["refs"]],
                request_sha256=data["request_sha256"],
            )
        )
        batches.append(PlannedBatch(batch_id=batch_id, **data))
    return BatchPlan(
        source=identity,
        blocks_sha256=fingerprint([b.model_dump(mode="json") for b in blocks]),
        config=config,
        limits=limits,
        batches=batches,
        total_slices=len(refs),
        total_requests=len(refs),
        eligible_chars=sum(len(r.text) for r in refs),
        excluded_blocks=[
            dict(
                block_id=b.block_id,
                reason="blank_text" if not b.text.strip() else b.aggregation_role,
            )
            for b in blocks
            if b.aggregation_role != "primary" or not b.text.strip()
        ],
    )


def check_approval(approval, identity, subject, plan):
    m1.check_approval(approval, identity, subject)
    if (
        approval.plan != plan
        or approval.limits != plan.limits
        or approval.config != plan.config
    ):
        raise Hold("current approval does not bind the complete batch plan")


def engine_input(plan, batch):
    return dict(
        adapter_version=ADAPTER_VERSION,
        plan_sha256=fingerprint(plan.model_dump(mode="json")),
        batch=batch.model_dump(mode="json"),
        source=plan.source,
        config=plan.config.model_dump(mode="json"),
        limits=plan.limits.model_dump(mode="json"),
    )


def consolidate_batches(plan, records):
    """Recheck every batch and claim before claiming global input completeness."""
    if len(records) != len(plan.batches):
        raise Hold("missing or extra batches")
    sections, claims, refs = [], [], []
    for batch, record in zip(plan.batches, records, strict=True):
        if (
            set(record) != {"batch_id", "status", "review_status", "summary"}
            or record["batch_id"] != batch.batch_id
            or record["status"] != "checked"
            or record["review_status"] != "unreviewed"
        ):
            raise Hold("duplicate, reordered or unchecked batch")
        result = SummaryResult.model_validate(record["summary"])
        m1.checked_result(
            result, batch.refs, plan.config, fingerprint(engine_input(plan, batch))
        )
        if (
            tuple(sha256(request_bytes(r, plan.config)) for r in result.refs)
            != batch.request_sha256
        ):
            raise Hold("batch request hashes changed")
        sections.extend(result.sections)
        claims.extend(c for section in result.sections for c in section.claims)
        refs.extend(result.refs)
    if (
        len(refs) != plan.total_slices
        or len({r.ref_id for r in refs}) != plan.total_slices
        or sum(len(r.text) for r in refs) != plan.eligible_chars
    ):
        raise Hold("global slice coverage conflict")
    # Keep batch claims intact: exact wording can still express distinct contexts.
    # Existing consolidate only supplies conflict diagnostics across batch boundaries.
    _, issues = m1.consolidate(sections)
    if issues:
        raise Hold("global claims require attention")
    cited = {r for claim in claims for r in claim.refs}
    ids = {r.ref_id for r in refs}
    if not cited <= ids:
        raise Hold("foreign global claim reference")
    return dict(
        status="completed",
        review_status="unreviewed",
        provider="fake",
        source=plan.source,
        plan_sha256=fingerprint(plan.model_dump(mode="json")),
        batch_ids=[b.batch_id for b in plan.batches],
        refs=[r.model_dump(mode="json") for r in refs],
        claims=[c.model_dump(mode="json") for c in claims],
        rejected_claims=[r for section in sections for r in section.rejected],
        uncertainties=[u for section in sections for u in section.uncertainties],
        coverage=dict(
            input_refs=plan.total_slices,
            processed_refs=len(sections),
            input_chars=plan.eligible_chars,
            processed_chars=sum(len(r.text) for r in refs),
            complete_input=True,
            cited_refs=len(cited),
            uncited_refs=sorted(ids - cited),
            input_coverage=len(sections) / plan.total_slices,
            citation_coverage=len(cited) / plan.total_slices,
            excluded_blocks=list(plan.excluded_blocks),
        ),
        warnings=[
            "FakeLLM mechanical excerpts; human review and subject-matter acceptance pending."
        ],
    )


def run(args):
    source = checked_path(explicit_root(args.source_root))
    target = checked_path(explicit_root(args.output_root))
    approval_path = checked_path(args.approval)
    if (
        source.is_relative_to(target)
        or target.is_relative_to(source)
        or approval_path.is_relative_to(source)
        or approval_path.is_relative_to(target)
    ):
        raise Hold("source, approval and new summary root must be isolated")
    approval_bytes = private_bytes(approval_path, 8 * 1024 * 1024)
    approval = BatchApproval.model_validate(mvp._json(approval_bytes))
    started = time.monotonic()
    with mvp.output_root(source) as (_, before):
        # Verify the complete stored source once; retain the lock and compare its
        # complete byte inventory afterwards instead of repeating Reader traversal.
        identity, blocks, doc = m1.read_source(
            source, args.source_id, args.parsed_version_id, args.actor
        )
        plan = make_plan(identity, blocks, doc, approval.config, approval.limits)
        check_approval(approval, identity, args.actor, plan)
        evidence = dict(
            plan=plan.model_dump(mode="json"),
            blocks=[b.model_dump(mode="json") for b in blocks],
        )
        if len(canonical(evidence)) > plan.limits.evidence_bytes:
            raise Hold("source evidence output limit exceeded")
        intent = dict(
            adapter_version=ADAPTER_VERSION,
            summary_approval_sha256=sha256(approval_bytes),
            evidence_sha256=fingerprint(evidence),
            implementation_revision=approval.implementation_revision,
            implementation_sha256=approval.implementation_sha256,
        )
        historical = mvp.ProcessingApproval.model_validate(
            mvp.load(source, "approval.json")
        )
        if (
            len(canonical(evidence))
            + len(approval_bytes)
            + len(canonical(intent))
            + 1024
            > plan.limits.stored_output_bytes
        ):
            raise Hold("initial stored output budget exceeded")
        calls, output_bytes = 0, 0

        def deadline():
            if time.monotonic() - started >= plan.limits.wall_seconds:
                raise Hold("total wall deadline exceeded")

        def before_call():
            nonlocal calls
            deadline()
            if min(approval.valid_until, historical.valid_until) <= datetime.now(UTC):
                raise Hold("approval chain expired during run")
            if calls >= plan.limits.requests:
                raise Hold("total request budget exceeded")
            calls += 1
            return plan.limits.wall_seconds - (time.monotonic() - started)

        def after_reply(raw):
            nonlocal output_bytes
            output_bytes += len(raw.encode())
            if output_bytes > plan.limits.raw_output_bytes:
                raise Hold("total raw output limit exceeded")
            deadline()

        def after_section(section):
            if section.rejected or section.uncertainties or not section.claims:
                raise Hold("section requires attention; no unchecked continuation")

        def stored_bytes():
            return sum(p.stat().st_size for p in target.rglob("*") if p.is_file())

        def unchanged():
            deadline()
            check_approval(approval, identity, args.actor, plan)
            # Revalidate expiry as well as original bytes, without changing the old attestation.
            m1.historical_approval(
                source,
                mvp.load(source, "intent.json"),
                mvp.actor_for(mvp.load(source, "intent.json"), args.actor),
            )
            if mvp.inventory(source) != before:
                raise Hold("source changed during batch summary")
            deadline()

        deadline()
        with m1.summary_root(target) as create:
            if not create:
                manifest = mvp.load(target, "manifest.json")
                observed = mvp.inventory(target)
                observed.pop("manifest.json")
                if (
                    observed != manifest
                    or mvp.load(target, "intent.json") != intent
                    or mvp.load(target, "evidence.json") != evidence
                ):
                    raise Hold(
                        "incomplete or changed batch root; retain evidence; no restart"
                    )
                records = []
                for batch in plan.batches:
                    record = mvp.load(target, f"batch-{batch.ordinal:03}.json")
                    state = mvp.load(target, f"batch-{batch.ordinal:03}-state.json")
                    if record["status"] != "candidate" or state != dict(
                        batch_id=batch.batch_id, phase="checked"
                    ):
                        raise Hold("cached batch not checked")
                    records.append(dict(record, status="checked"))
                report = consolidate_batches(plan, records)
                if (
                    report != mvp.load(target, "summary.json")
                    or mvp.load(target, "state.json")["phase"] != "ready"
                ):
                    raise Hold("cached global evidence conflict")
                unchanged()
                return report
            publish_bytes(target / "approval.json", approval_bytes)
            publish_bytes(target / "intent.json", canonical(intent))
            publish_bytes(target / "evidence.json", canonical(evidence))
            write_state(
                target / "state.json",
                dict(phase="pending", planned_batches=len(plan.batches)),
            )
            records = []
            active = None
            try:
                for batch in plan.batches:
                    active = batch
                    deadline()
                    write_state(
                        target / f"batch-{batch.ordinal:03}-state.json",
                        dict(batch_id=batch.batch_id, phase="running"),
                    )
                    # Each batch owns a normal M1 engine run and cache namespace.
                    result = generate_refs(
                        SummaryStore(target / f"engine-{batch.ordinal:03}"),
                        batch.refs,
                        engine_input(plan, batch),
                        plan.config,
                        FakeLLM(),
                        title="One verified lecture batch",
                        before_call=before_call,
                        after_reply=after_reply,
                        after_section=after_section,
                    ).result
                    record = dict(
                        batch_id=batch.batch_id,
                        status="checked",
                        review_status="unreviewed",
                        summary=result.model_dump(mode="json"),
                    )
                    # Save candidates before checking; even rejected evidence survives HOLD.
                    publish_bytes(
                        target / f"batch-{batch.ordinal:03}.json",
                        canonical(dict(record, status="candidate")),
                    )
                    m1.checked_result(
                        result,
                        batch.refs,
                        plan.config,
                        fingerprint(engine_input(plan, batch)),
                    )
                    write_state(
                        target / f"batch-{batch.ordinal:03}-state.json",
                        dict(batch_id=batch.batch_id, phase="checked"),
                    )
                    # Candidate bytes are immutable; validation state lives separately.
                    if stored_bytes() > plan.limits.stored_output_bytes:
                        raise Hold("total stored output budget exceeded")
                    records.append(record)
                    active = None
                report = consolidate_batches(plan, records)
                if len(canonical(report)) > plan.limits.evidence_bytes:
                    raise Hold("consolidated output byte limit exceeded")
                # Reserve the final report, manifest and bounded state growth
                # before publishing any completed lecture evidence.
                reserved = (
                    len(canonical(report))
                    + len(canonical(mvp.inventory(target)))
                    + 4096
                )
                if stored_bytes() + reserved > plan.limits.stored_output_bytes:
                    raise Hold("total stored output budget exceeded")
                unchanged()
                # Cache consumes immutable candidates plus checked state, never an unchecked result.
                publish_bytes(target / "summary.json", canonical(report))
                write_state(
                    target / "state.json",
                    dict(
                        phase="ready",
                        planned_batches=len(plan.batches),
                        completed_batches=len(records),
                        requests=calls,
                        raw_output_bytes=output_bytes,
                    ),
                )
                publish_bytes(
                    target / "manifest.json", canonical(mvp.inventory(target))
                )
                return report
            except BaseException as error:
                if active:
                    write_state(
                        target / f"batch-{active.ordinal:03}-state.json",
                        dict(
                            batch_id=active.batch_id,
                            phase="HOLD",
                            error=type(error).__name__,
                        ),
                    )
                write_state(
                    target / "state.json",
                    dict(
                        phase="HOLD",
                        planned_batches=len(plan.batches),
                        completed_batches=len(records),
                        requests=calls,
                        error=type(error).__name__,
                    ),
                )
                raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "run"))
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--parsed-version-id", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--limits", type=Path)
    args = parser.parse_args(argv)
    previous = os.umask(0o077)
    try:
        if args.command == "plan":
            if args.approval or args.output_root:
                raise Hold("planning does not create approvals or summary roots")
            config = (
                SummaryConfig.model_validate(
                    mvp._json(private_bytes(checked_path(args.config), 65536))
                )
                if args.config
                else SummaryConfig(max_chunks=32)
            )
            limits = (
                BatchLimits.model_validate(
                    mvp._json(private_bytes(checked_path(args.limits), 65536))
                )
                if args.limits
                else BatchLimits()
            )
            source = checked_path(explicit_root(args.source_root))
            with mvp.output_root(source) as (_, before):
                identity, blocks, doc = m1.read_source(
                    source, args.source_id, args.parsed_version_id, args.actor
                )
                plan = make_plan(identity, blocks, doc, config, limits)
                if mvp.inventory(source) != before:
                    raise Hold("source changed during planning")
                revision, digest = mvp.implementation_identity()
                report = dict(
                    status="approval_required",
                    implementation_revision=revision,
                    implementation_sha256=digest,
                    plan=plan.model_dump(mode="json"),
                )
        else:
            if not args.approval or not args.output_root or args.config or args.limits:
                raise Hold(
                    "run requires exact approval and output root; config/limits come from approval"
                )
            report = run(args)
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (
        m1.ContentStoreError,
        m1.ReadFault,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        subprocess.SubprocessError,
        RuntimeError,
    ) as error:
        print(
            json.dumps(
                dict(
                    status="HOLD",
                    success=False,
                    reason=str(error)
                    if isinstance(error, Hold)
                    else type(error).__name__,
                    recovery="retain all evidence; no automatic retry or continuation",
                )
            ),
            file=sys.stderr,
        )
        return 2
    finally:
        os.umask(previous)


if __name__ == "__main__":
    raise SystemExit(main())
