"""Verified CS50 lecture execution; bounded pilot remains a separate entry point."""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt

from src.core.config_knowledge import KnowledgeSettings
from src.model_knowledge.data_knowledge import ChunkKnowledgeResult
from src.tools_knowledge.bind_cs50_transcript import (
    build_cs50_knowledge_chunks,
    build_cs50_knowledge_document,
    load_knowledge_transcript,
    portable_input,
    resolve_knowledge_input,
)
from src.tools_knowledge.cs50_budget import (
    BudgetExhausted,
    BudgetIdentity,
    BudgetJournal,
)
from src.tools_knowledge.cs50_checkpoint import (
    CheckpointConflict,
    CheckpointStore,
    Contract,
    JobIdentity,
    atomic_json,
    fingerprint,
)
from src.tools_knowledge.cs50_extraction_provider import (
    OpenAIHTTPProvider,
    RequestBudget,
    messages_for,
)
from src.tools_lecture.execute_cs50 import safe_path


class LectureRunConfig(Contract):
    schema_version: Literal[1] = 1
    provider: Literal["openai_http"] = "openai_http"
    model: str = "gpt-4o-mini"
    evidence_mode: Literal["chunk", "segment_v1"] = "segment_v1"
    execute_llm: bool = False
    max_requests: StrictInt = Field(default=1, ge=1, le=100000)
    token_budget: StrictInt = Field(default=60000, ge=1, le=100000000)
    input_limit: StrictInt = Field(default=28000, ge=1, le=30000)
    output_limit: StrictInt = Field(default=1200, ge=1, le=2000)
    max_seconds: StrictInt = Field(default=120, ge=1, le=3600)
    settings: KnowledgeSettings = Field(default_factory=KnowledgeSettings)


@dataclass
class PlannedLecture:
    plan: object
    input: object
    workspace: Path
    chunks: list
    segments: dict
    identity: JobIdentity
    config: LectureRunConfig


def prepare_lecture(plan, input, *, workspace, config):
    """Real import-receipt validation and chunker; full identity before any dispatch."""
    workspace = Path(workspace).absolute()
    input = resolve_knowledge_input(input, workspace=workspace)
    chunks = build_cs50_knowledge_chunks(
        plan, input, config.settings, workspace=workspace
    )
    if not chunks or any(len(c.text) > 6000 for c in chunks):
        raise CheckpointConflict(
            "No nonempty bounded chunk plan; no implicit splitting/fallback"
        )
    transcript = load_knowledge_transcript(plan, input, workspace=workspace)
    segments = {s.seg_id: s for s in transcript.segments}
    portable = portable_input(input, workspace=workspace)
    identity = JobIdentity(
        **{
            k: getattr(input, k)
            for k in (
                "course_id",
                "section_key",
                "lecture_id",
                "resource_id",
                "source_id",
                "transcript_sha256",
            )
        },
        raw_sha256=input.raw_sha256,
        input_binding_sha256=fingerprint(portable.model_dump(mode="json")),
        chunking=config.settings.model_dump(mode="json"),
        chunk_plan_sha256=fingerprint([c.model_dump(mode="json") for c in chunks]),
        selected_chunks=tuple(c.chunk_id for c in chunks),
        prompt_version="knowledge_extraction_v1",
        prompt_sha256=fingerprint(
            [
                messages_for(
                    c,
                    segments=segments if config.evidence_mode == "segment_v1" else None,
                )
                for c in chunks
            ]
        ),
        result_schema_sha256=fingerprint(ChunkKnowledgeResult.model_json_schema()),
        evidence_mode=config.evidence_mode,
        evidence_version="cs50_segment_evidence_v1"
        if config.evidence_mode == "segment_v1"
        else "chunk_v1",
        provider=config.provider,
        model=config.model,
        execution_mode="llm" if config.execute_llm else "offline",
        request_limits=config.model_dump(mode="json", exclude={"settings"}),
    )
    return PlannedLecture(plan, input, workspace, chunks, segments, identity, config)


def checked_output(job, directory):
    path = Path(directory).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise CheckpointConflict("Symlink output root forbidden")
    repo_data = Path(__file__).resolve().parents[2] / "data"
    roots = [repo_data]
    for course in job.plan.courses:
        roots.append(
            course.artifact_root
            if course.artifact_root.is_absolute()
            else job.workspace / course.artifact_root
        )
    if any(
        path.resolve().is_relative_to(root.resolve())
        or root.resolve().is_relative_to(path.resolve())
        for root in roots
    ):
        raise CheckpointConflict(
            "Knowledge output must be separate from all source roots"
        )
    return path


def ensure_contract(directory, name, value):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = safe_path(directory, directory / name)
    if path.exists():
        import json

        try:
            actual = json.loads(path.read_bytes())
        except (OSError, ValueError) as error:
            raise CheckpointConflict("Invalid immutable execution contract") from error
        if actual != value:
            raise CheckpointConflict("Immutable execution contract conflict")
    else:
        atomic_json(path, value)


def lecture_budget(jobs, directory):
    if not jobs or len({j.identity.job_id for j in jobs}) != len(jobs):
        raise CheckpointConflict("Explicit unique budget jobs required")
    cfg = jobs[0].config
    if any(j.config != cfg for j in jobs):
        raise CheckpointConflict("All scope jobs must share one configuration")
    identity = BudgetIdentity(
        scope_sha256=fingerprint([j.identity.job_id for j in jobs]),
        allowed_jobs=tuple(j.identity.job_id for j in jobs),
        max_requests=cfg.max_requests,
        max_tokens=cfg.token_budget,
    )
    return BudgetJournal(checked_output(jobs[0], directory), identity)


def check_runtime(budget, seconds, *, dispatch=False):
    """Persistent scope wall-clock deadline, in addition to CLI process-group timeout."""
    import json

    with budget.locked() as (state, _):
        path = budget.directory / "runtime.v1.json"
        if path.is_symlink():
            raise CheckpointConflict("Symlink runtime receipt")
        if path.exists():
            try:
                value = json.loads(path.read_bytes())
                if (
                    set(value)
                    != {"schema_version", "budget_id", "started_at", "max_seconds"}
                    or value["schema_version"] != 1
                    or value["budget_id"] != budget.identity.budget_id
                    or value["max_seconds"] != seconds
                    or type(value["started_at"]) not in (int, float)
                    or not 0 < value["started_at"] <= time.time()
                ):
                    raise ValueError("runtime contract")
            except (OSError, ValueError, TypeError) as error:
                raise CheckpointConflict(
                    "Invalid persistent runtime contract"
                ) from error
        else:
            if state.attempts:
                raise CheckpointConflict(
                    "Runtime receipt missing after budget dispatch"
                )
            value = {
                "schema_version": 1,
                "budget_id": budget.identity.budget_id,
                "started_at": time.time(),
                "max_seconds": seconds,
            }
            atomic_json(path, value)
        if dispatch and time.time() >= value["started_at"] + seconds:
            raise BudgetExhausted("Persistent scope runtime exhausted")


def validate_chunk(job, chunk, values):
    result = ChunkKnowledgeResult.model_validate(values["result"])
    audit = []
    checked = build_cs50_knowledge_document(
        job.input,
        [chunk],
        [result],
        plan=job.plan,
        workspace=job.workspace,
        evidence_mode=job.config.evidence_mode,
        evidence_audit=audit,
    ).chunks[0]
    evidence = {
        "schema_version": 1,
        "source_id": job.input.source_id,
        "chunk_id": chunk.chunk_id,
        "evidence_mode": job.config.evidence_mode,
        "items": audit,
    }
    if (
        checked != result
        or values["evidence"] != evidence
        or not isinstance(values["provider"], dict)
    ):
        raise CheckpointConflict("Chunk result/evidence/source conflict")
    return checked


def verify_budget(budget, store, chunk_id, *, validated=False):
    record = store.state.chunks[chunk_id]
    if record.reservation is None:
        if store.identity.execution_mode == "llm" and record.status in (
            "prepared",
            "done",
        ):
            raise CheckpointConflict("LLM checkpoint lacks reservation")
        return
    reference = record.reservation
    state = budget.snapshot()
    key = fingerprint([store.identity.job_id, chunk_id])
    attempt = state.attempts.get(key)
    if (
        reference.get("budget_id") != budget.identity.budget_id
        or reference.get("attempt_id") != key
        or attempt is None
        or attempt.reserved_tokens != reference["reserved_tokens"]
    ):
        raise CheckpointConflict("Checkpoint and budget attempt conflict")
    if record.status == "done" and validated:
        budget.finish(
            store.identity.job_id,
            chunk_id,
            status="done",
            usage=record.metadata.get("usage"),
        )
    elif record.status == "unknown" and attempt.status == "reserved":
        budget.finish(store.identity.job_id, chunk_id, status="unknown")


def run_lecture(job, directory, budget, *, indices=None, provider_factory=None):
    """No automatic retries. Injection is reserved for offline Fake-HTTP tests."""
    cfg = job.config
    if cfg.execute_llm and (
        os.environ.get("CS50_LECTURE_EXECUTE_LLM") != "1"
        or provider_factory is not None
    ):
        raise CheckpointConflict(
            "Real API execution requires isolated parent authorization"
        )
    directory = checked_output(job, directory)
    if (
        directory == budget.directory
        or directory.is_relative_to(budget.directory)
        or budget.directory.is_relative_to(directory)
    ):
        raise CheckpointConflict("Job and shared budget roots must be separate")
    if job.identity.job_id not in budget.identity.allowed_jobs:
        raise CheckpointConflict("Job is not in explicit shared budget scope")
    indices = list(range(len(job.chunks))) if indices is None else list(indices)
    if (
        not indices
        or len(set(indices)) != len(indices)
        or any(type(i) is not int or not 0 <= i < len(job.chunks) for i in indices)
    ):
        raise ValueError("Invalid or duplicate chunk window")
    ensure_contract(
        directory,
        "lecture.contract.v1.json",
        {
            "schema_version": 1,
            "identity": job.identity.model_dump(mode="json"),
            "input": portable_input(job.input, workspace=job.workspace).model_dump(
                mode="json"
            ),
            "budget_identity": budget.identity.model_dump(mode="json"),
        },
    )
    check_runtime(budget, cfg.max_seconds)
    provider = None
    with CheckpointStore(
        directory / "checkpoint", job.identity, job.chunks
    ).locked() as store:
        cached = {}
        for chunk in job.chunks:
            verify_budget(budget, store, chunk.chunk_id)
            cached[chunk.chunk_id] = store.reuse(
                chunk.chunk_id,
                lambda values, chunk=chunk: validate_chunk(job, chunk, values),
            )
            if cached[chunk.chunk_id] is not None:
                verify_budget(budget, store, chunk.chunk_id, validated=True)
        try:
            for index in indices:
                chunk = job.chunks[index]
                if cached[chunk.chunk_id] is not None:
                    continue
                local = RequestBudget(1, 64000, cfg.input_limit, cfg.output_limit)

                def reserve(reservation, chunk=chunk):
                    check_runtime(budget, cfg.max_seconds, dispatch=True)
                    reference = budget.reserve(
                        job.identity.job_id, chunk.chunk_id, reservation
                    )
                    store.reserve(chunk.chunk_id, reference)

                local.before_dispatch = reserve
                if cfg.execute_llm or provider_factory is not None:
                    factory = provider_factory or OpenAIHTTPProvider
                    provider = factory(
                        api_key=os.environ.get("OPENAI_API_KEY"),
                        model=cfg.model,
                        budget=local,
                        **(
                            {"segments": job.segments}
                            if cfg.evidence_mode == "segment_v1"
                            else {}
                        ),
                    )
                record = {
                    "chunk_id": chunk.chunk_id,
                    "usage": None,
                    "result_origin": "LLM" if cfg.execute_llm else "synthetic",
                }
                try:
                    if provider:
                        result = provider.extract(chunk, record)
                    else:
                        result = ChunkKnowledgeResult.model_validate(
                            {
                                "analysis": {
                                    "chunk_id": chunk.chunk_id,
                                    "relevant": False,
                                },
                                "extraction": None,
                            }
                        )
                    raw = record.pop("provider_fields", None) or result.model_dump(
                        mode="json", exclude_unset=True
                    )
                    if cfg.evidence_mode == "chunk":
                        result.analysis.chunk_id = chunk.chunk_id
                        if result.extraction is not None:
                            result.extraction.chunk_id = chunk.chunk_id
                    audit = []
                    bound = build_cs50_knowledge_document(
                        job.input,
                        [chunk],
                        [result],
                        plan=job.plan,
                        workspace=job.workspace,
                        evidence_mode=cfg.evidence_mode,
                        evidence_audit=audit,
                    ).chunks[0]
                    record["validated"] = True
                    values = {
                        "provider": raw,
                        "result": bound.model_dump(mode="json"),
                        "evidence": {
                            "schema_version": 1,
                            "source_id": job.input.source_id,
                            "chunk_id": chunk.chunk_id,
                            "evidence_mode": cfg.evidence_mode,
                            "items": audit,
                        },
                    }
                    store.complete(
                        chunk.chunk_id,
                        values,
                        record,
                        lambda values, chunk=chunk: validate_chunk(job, chunk, values),
                    )
                    verify_budget(budget, store, chunk.chunk_id, validated=True)
                except Exception:
                    store.interrupted(chunk.chunk_id)
                    verify_budget(budget, store, chunk.chunk_id)
                    raise
                finally:
                    if provider:
                        provider.close()
                        provider = None
            return {
                "job_id": job.identity.job_id,
                "status": store.state.status,
                "expected_chunks": len(job.chunks),
                "done_chunks": sum(
                    c.status == "done" for c in store.state.chunks.values()
                ),
            }
        finally:
            if provider:
                provider.close()
