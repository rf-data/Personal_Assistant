"""Read-only checked SRT input binding; no runner dispatch or inference calls."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from src.model_discovery.cs50 import Provenance
from src.model_knowledge.data_knowledge import (
    ChunkKnowledgeResult,
    TranscriptKnowledgeDocument,
)
from src.model_transcribe.data_transcribe import (
    TranscriptDocument,
    TranscriptProvenance,
)
from src.tools_knowledge.find_knowledge import (
    attach_chunk_provenance,
    build_transcript_chunks,
    make_visual_candidate,
    validate_extraction,
)
from src.tools_lecture.adapt_cs50 import CS50AdapterPlan, CS50TranscriptBinding, Sha256
from src.tools_lecture.execute_cs50 import (
    ExecutionConflict,
    digest,
    safe_path,
    validate_document,
)


class CS50KnowledgeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    artifact_version: Literal[1] = 1
    course_id: str
    section_key: str
    lecture_id: str
    resource_id: str
    source_id: str
    media_id: str | None
    transcript_url: str
    language: str
    transcript_provenance: TranscriptProvenance
    discovery_provenance: tuple[Provenance, ...]
    raw_srt_path: Path
    transcript_json_path: Path
    receipt_path: Path
    raw_sha256: Sha256
    transcript_sha256: Sha256
    binding: CS50TranscriptBinding

    @model_validator(mode="after")
    def checked_identity(self):
        binding = self.binding
        for field in (
            "course_id",
            "section_key",
            "lecture_id",
            "resource_id",
            "source_id",
            "media_id",
            "transcript_url",
            "language",
        ):
            if getattr(self, field) != getattr(binding, field):
                raise ValueError(f"Knowledge input contradicts binding: {field}")
        provenance = self.transcript_provenance
        if (
            provenance.source_url != self.transcript_url
            or provenance.language != self.language
            or provenance.transcript_source.value != "official_subtitle"
            or provenance.media_format != "srt"
            or provenance.source_file != str(binding.raw_srt_path)
            or provenance.media_id != self.media_id
            or self.discovery_provenance != binding.provenance
        ):
            raise ValueError("Knowledge input provenance contradicts checked SRT")
        return self


class CS50KnowledgeInputManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    inputs: tuple[CS50KnowledgeInput, ...]

    @model_validator(mode="after")
    def unique_sources(self):
        if len({item.source_id for item in self.inputs}) != len(self.inputs):
            raise ValueError("Duplicate Knowledge source identity")
        return self


def bind_cs50_knowledge_input(plan, binding, *, workspace):
    """Validate completed receipts and both artifacts; never modify any of them."""
    import json

    plan = CS50AdapterPlan.model_validate_json(plan.model_dump_json())
    course = next(
        (c for c in plan.courses if c.lecture_course.course_id == binding.course_id),
        None,
    )
    if course is None or binding not in course.bindings:
        raise ExecutionConflict("Binding not present in checked adapter plan")
    workspace = Path(workspace).absolute()
    root = course.artifact_root
    root = root if root.is_absolute() else workspace / root
    safe_path(workspace, root)

    def target(path):
        return safe_path(root, path if path.is_absolute() else workspace / path)

    raw = target(binding.raw_srt_path)
    normalized = target(binding.transcript_json_path)
    receipt_path = target(raw.parent / "execution.v1.json")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ExecutionConflict(
            f"Missing or invalid execution receipt: {receipt_path}"
        ) from error
    if receipt.get("schema_version") != 1 or receipt.get(
        "binding"
    ) != binding.model_dump(mode="json"):
        raise ExecutionConflict("Receipt version/identity/provenance conflict")
    hashes = {}
    for task in course.tasks:
        if task.resource_id != binding.resource_id:
            continue
        action = task.task.actions[0].value
        record = receipt.get("actions", {}).get(task.task_id, {})
        if record.get("status") != "done" or record.get("action") != action:
            raise ExecutionConflict(f"Task not successfully completed: {task.task_id}")
        path = raw if action == "download" else normalized
        if not path.is_file() or digest(path) != record.get("sha256"):
            raise ExecutionConflict(f"Missing artifact or hash conflict: {path}")
        hashes[action] = record["sha256"]
        if action == "parse_subtitle" and record.get("input_sha256") != hashes.get(
            "download"
        ):
            raise ExecutionConflict(
                "Import input hash does not match completed download"
            )
    if set(hashes) != {"download", "parse_subtitle"}:
        raise ExecutionConflict("Exactly two completed SRT actions are required")
    document = validate_document(normalized, binding, raw)
    return CS50KnowledgeInput(
        **{
            field: getattr(binding, field)
            for field in (
                "course_id",
                "section_key",
                "lecture_id",
                "resource_id",
                "source_id",
                "media_id",
                "transcript_url",
                "language",
            )
        },
        transcript_provenance=document.provenance,
        discovery_provenance=binding.provenance,
        raw_srt_path=raw,
        transcript_json_path=normalized,
        receipt_path=receipt_path,
        raw_sha256=hashes["download"],
        transcript_sha256=hashes["parse_subtitle"],
        binding=binding,
    )


def load_knowledge_transcript(plan, input, *, workspace):
    checked = bind_cs50_knowledge_input(plan, input.binding, workspace=workspace)
    if checked != input:
        raise ExecutionConflict(
            "Knowledge manifest no longer matches checked artifacts"
        )
    return TranscriptDocument.model_validate_json(
        checked.transcript_json_path.read_bytes()
    )


def build_cs50_knowledge_chunks(plan, input, settings, *, workspace):
    transcript = load_knowledge_transcript(plan, input, workspace=workspace)
    # Silent cues retain their IDs/times in the source; they cannot provide content evidence.
    nonempty = [s for s in transcript.segments if s.text.strip()]
    if len({s.seg_id for s in transcript.segments}) != len(transcript.segments):
        raise ExecutionConflict("Duplicate transcript segment IDs")
    if settings.target_duration <= 0 or settings.overlap_segments < 1:
        raise ValueError("Positive duration and overlap_segments >= 1 required")
    chunks = build_transcript_chunks(
        settings, transcript.model_copy(update={"segments": nonempty})
    )
    if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
        raise ExecutionConflict("Duplicate chunk IDs")
    return chunks


def build_cs50_knowledge_document(
    input,
    chunks,
    results,
    *,
    plan,
    workspace,
    evidence_mode="chunk",
    evidence_audit=None,
):
    """Attach trusted chunk evidence to supplied extraction results; never call an LLM."""
    if evidence_mode not in ("chunk", "segment_v1"):
        raise ValueError("Unknown evidence mode")
    input = CS50KnowledgeInput.model_validate(input.model_dump())
    load_knowledge_transcript(plan, input, workspace=workspace)
    if digest(input.transcript_json_path) != input.transcript_sha256:
        raise ExecutionConflict("Transcript changed before evidence binding")
    if digest(input.raw_srt_path) != input.raw_sha256:
        raise ExecutionConflict("Raw SRT changed before evidence binding")
    document = validate_document(
        input.transcript_json_path, input.binding, input.raw_srt_path
    )
    if document.provenance != input.transcript_provenance:
        raise ExecutionConflict("Transcript provenance changed before evidence binding")
    segments = {s.seg_id: s for s in document.segments if s.text.strip()}
    for chunk in chunks:
        if not chunk.segment_ids or any(
            seg_id not in segments for seg_id in chunk.segment_ids
        ):
            raise ExecutionConflict("Unknown or empty cue cannot provide evidence")
        selected = [segments[seg_id] for seg_id in chunk.segment_ids]
        if (
            chunk.start != selected[0].start
            or chunk.end != selected[-1].end
            or chunk.text != "\n".join(s.text for s in selected)
        ):
            raise ExecutionConflict(
                "Chunk text/timestamps contradict original segments"
            )
    by_id = {chunk.chunk_id: chunk for chunk in chunks}
    if len(by_id) != len(chunks):
        raise ExecutionConflict("Duplicate chunk IDs")
    output = []
    visual_candidates = []
    seen = set()
    for supplied in results:
        result = ChunkKnowledgeResult.model_validate(supplied.model_dump())
        chunk_id = result.analysis.chunk_id
        if chunk_id not in by_id or chunk_id in seen:
            raise ExecutionConflict("Unknown or duplicate result chunk identity")
        seen.add(chunk_id)
        if evidence_mode == "segment_v1":
            from src.tools_knowledge.cs50_precise_evidence import (
                bind_precise_candidates,
            )

            audit_start = len(evidence_audit) if evidence_audit is not None else 0
            result = bind_precise_candidates(
                supplied.model_dump(), by_id[chunk_id], segments, evidence_audit
            )
            if evidence_audit is not None:
                for proof in evidence_audit[audit_start:]:
                    proof["source_id"] = input.source_id
            validated = validate_extraction(result)
        else:
            validated = validate_extraction(
                attach_chunk_provenance(result, by_id[chunk_id])
            )
        output.append(validated)
        candidate = make_visual_candidate(validated, by_id[chunk_id])
        if candidate is not None:
            visual_candidates.append(candidate)
    return TranscriptKnowledgeDocument(
        source_id=input.source_id,
        transcript_url=input.transcript_url,
        media_id=input.media_id,
        language=input.language,
        transcript_provenance=input.transcript_provenance,
        course_id=input.course_id,
        lecture_id=input.lecture_id,
        chunks=output,
        visual_candidates=visual_candidates,
    )


def save_knowledge_manifest(manifest, destination):
    manifest = CS50KnowledgeInputManifest.model_validate(manifest.model_dump())
    with Path(destination).open("x", encoding="utf-8") as output:
        output.write(manifest.model_dump_json(indent=2) + "\n")
