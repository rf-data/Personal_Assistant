"""Immutable source plans, verified vector artifacts and fail-closed Qdrant resume."""

import fcntl
import math
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from src.model_discovery.cs50_index import CollectionContract, Hash, TranscriptPayload
from src.tools_knowledge.cs50_checkpoint import Contract, atomic_json, fingerprint
from src.tools_rag.cs50_collection import check_collection, ensure_collection
from src.tools_rag.cs50_embeddings import (
    checked_vectors,
    chunking_configuration,
    map_transcript,
    source_time_window,
)


class SourceIndexPlan(Contract):
    input: dict
    units: tuple[TranscriptPayload, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identity(self):
        first = self.units[0]
        for p in self.units:
            for key in (
                "course_id",
                "section_key",
                "lecture_id",
                "resource_id",
                "source_id",
                "media_id",
                "language",
                "raw_sha256",
                "transcript_sha256",
            ):
                if getattr(p, key) != self.input.get(key):
                    raise ValueError("Source/unit identity conflict")
            if p.original_url != self.input.get("transcript_url"):
                raise ValueError("Source URL conflict")
            for key in (
                "receipt_sha256",
                "input_binding_sha256",
                "chunk_plan_sha256",
                "chunking",
                "transcript_provenance",
                "provenance_sha256",
                "discovery_provenance",
                "source_origin",
            ):
                if getattr(p, key) != getattr(first, key):
                    raise ValueError(
                        "Inconsistent source hashes/configuration/provenance"
                    )
        for chunk_id in {p.chunk_id for p in self.units}:
            units = [p for p in self.units if p.chunk_id == chunk_id]
            if [p.unit_index for p in units] != list(range(len(units))) or any(
                p.unit_count != len(units) for p in units
            ):
                raise ValueError("Missing/duplicate embedding unit")
            cursor = 0
            for p in units:
                if p.char_start < cursor:
                    raise ValueError("Overlapping/out-of-order embedding offsets")
                if p.original_chunk_text[cursor : p.char_start].strip():
                    raise ValueError("Missing original content in embedding windows")
                cursor = p.char_end
            if units[-1].original_chunk_text[cursor:].strip():
                raise ValueError("Missing trailing original content")
        return self


class IngestionPlan(Contract):
    schema_version: Literal[1] = 1
    adapter_plan_sha256: Hash
    scope: Literal["lecture", "course", "six_courses"]
    collection: CollectionContract
    sources: tuple[SourceIndexPlan, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identities(self):
        source_ids = [s.input["source_id"] for s in self.sources]
        ids = [p.point_id for s in self.sources for p in s.units]
        if len(set(source_ids)) != len(source_ids) or len(set(ids)) != len(ids):
            raise ValueError("Duplicate source/point identity")
        courses = {s.input["course_id"] for s in self.sources}
        if self.scope == "lecture" and len(self.sources) != 1:
            raise ValueError("Lecture scope requires one source")
        if self.scope == "course" and len(courses) != 1:
            raise ValueError("Course scope requires one course")
        if self.scope == "six_courses" and (
            len(self.sources) != 50
            or courses
            != {
                "cs50x",
                "cs50_python",
                "cs50_sql",
                "cs50_ai",
                "cs50_web",
                "cs50_cybersecurity",
            }
        ):
            raise ValueError("Six-course scope requires the exact 50-source contract")
        for source in self.sources:
            for p in source.units:
                p.check_collection(self.collection)
        return self

    @property
    def plan_id(self):
        return fingerprint(self.model_dump(mode="json"))

    @property
    def units(self):
        return tuple(p for source in self.sources for p in source.units)


def selected_bindings(adapter, *, course=None, section=None, all_six=False):
    if all_six and (course is not None or section is not None):
        raise ValueError("Choose explicit course/lecture OR all six")
    if not all_six and course is None:
        raise ValueError("Explicit course selection required")
    bindings = tuple(
        b
        for c in adapter.courses
        for b in c.bindings
        if (course is None or b.course_id == course)
        and (section is None or b.section_key == section)
    )
    if not bindings:
        raise ValueError("No matching course/lecture")
    if all_six and (len(adapter.courses) != 6 or len(bindings) != 50):
        raise ValueError("Six-course contract requires all 50 bindings")
    return bindings


def build_ingestion_plan(
    adapter,
    inputs,
    settings,
    embedder,
    *,
    workspace,
    course=None,
    section=None,
    all_six=False,
    contract=None,
    source_origin="official",
    max_units=25000,
):
    from src.tools_knowledge.bind_cs50_transcript import portable_input

    contract = contract or CollectionContract(embedding=embedder.config)
    bindings = selected_bindings(
        adapter, course=course, section=section, all_six=all_six
    )
    if len({i.source_id for i in inputs}) != len(inputs):
        raise ValueError("Duplicate provided source inputs")
    available = {i.source_id: i for i in inputs}
    missing = [b.source_id for b in bindings if b.source_id not in available]
    if missing:
        raise ValueError(f"Missing validated source inputs: {missing}")
    sources = []
    for b in bindings:
        input = available[b.source_id]
        if input.binding != b:
            raise ValueError("Input binding does not match selected adapter source")
        units = map_transcript(
            adapter,
            input,
            settings,
            embedder,
            workspace=workspace,
            source_origin=source_origin,
            contract=contract,
        )
        sources.append(
            SourceIndexPlan(
                input=portable_input(input, workspace=workspace).model_dump(
                    mode="json"
                ),
                units=tuple(units),
            )
        )
        if sum(len(s.units) for s in sources) > max_units:
            raise ValueError("Explicit embedding-unit budget exceeded")
    return IngestionPlan(
        adapter_plan_sha256=fingerprint(adapter.model_dump(mode="json")),
        scope="six_courses"
        if all_six
        else "lecture"
        if section is not None
        else "course",
        collection=contract,
        sources=tuple(sources),
    )


def revalidate_plan(plan, adapter, *, workspace, source_ids=None):
    from src.core.config_knowledge import KnowledgeSettings
    from src.tools_knowledge.bind_cs50_transcript import CS50PortableInput

    if plan.adapter_plan_sha256 != fingerprint(adapter.model_dump(mode="json")):
        raise ValueError("Adapter plan hash conflict")
    for source in plan.sources:
        if source_ids is not None and source.input["source_id"] not in source_ids:
            continue
        input = CS50PortableInput.model_validate(source.input)
        from src.tools_knowledge.bind_cs50_transcript import (
            build_cs50_knowledge_chunks,
            load_knowledge_transcript,
        )
        from src.tools_lecture.execute_cs50 import digest

        doc = load_knowledge_transcript(adapter, input, workspace=workspace)
        record = source.units[0].chunking
        if set(record) != {"target_duration", "max_duration", "overlap_segments"}:
            raise ValueError(
                "Only the complete actual chunker configuration belongs in index payloads"
            )
        settings = KnowledgeSettings.model_validate(record)
        if fingerprint(chunking_configuration(settings)) != fingerprint(record):
            raise ValueError("Incomplete/coerced chunking configuration")
        chunks = build_cs50_knowledge_chunks(
            adapter, input, settings, workspace=workspace
        )
        if (
            fingerprint([c.model_dump(mode="json") for c in chunks])
            != source.units[0].chunk_plan_sha256
        ):
            raise ValueError("Chunk plan hash conflict")
        from src.tools_knowledge.bind_cs50_transcript import resolve_knowledge_input

        resolved = resolve_knowledge_input(input, workspace=workspace)
        if digest(resolved.receipt_path) != source.units[0].receipt_sha256:
            raise ValueError("Execution receipt hash conflict")
        if (
            fingerprint(input.binding.model_dump(mode="json"))
            != source.units[0].input_binding_sha256
        ):
            raise ValueError("Inputbinding hash conflict")
        chunk_map = {c.chunk_id: c for c in chunks}
        if set(chunk_map) != {p.chunk_id for p in source.units}:
            raise ValueError("Incomplete source chunk coverage")
        segments = {s.seg_id: s for s in doc.segments if s.text.strip()}
        for unit in source.units:
            chunk = chunk_map.get(unit.chunk_id)
            if chunk is None or (
                chunk.text,
                tuple(chunk.segment_ids),
                chunk.start,
                chunk.end,
            ) != (
                unit.original_chunk_text,
                unit.original_chunk_segment_ids,
                unit.original_chunk_start,
                unit.original_chunk_end,
            ):
                raise ValueError("Original chunk reference conflict")
            spans, offset = [], 0
            for sid in chunk.segment_ids:
                s = segments[sid]
                if offset < unit.char_end and offset + len(s.text) > unit.char_start:
                    spans.append(s)
                offset += len(s.text) + 1
            if tuple(s.seg_id for s in spans) != unit.segment_ids or source_time_window(
                spans
            ) != (unit.start, unit.end):
                raise ValueError("Original segment/time reference conflict")
            if (
                fingerprint(doc.provenance.model_dump(mode="json"))
                != unit.provenance_sha256
            ):
                raise ValueError("Transcript provenance hash conflict")
            provenance = doc.provenance.model_dump(mode="json")
            if provenance.get("source_file", "").startswith(("/", "\\")):
                provenance["source_file"] = None
            if provenance != unit.transcript_provenance or fingerprint(
                unit.discovery_provenance
            ) != fingerprint(
                [p.model_dump(mode="json") for p in input.discovery_provenance]
            ):
                raise ValueError("Payload provenance conflicts with checked original")
    return plan


def checked_artifact_path(path, adapter, workspace):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlink index artifact path forbidden")
    roots = [Path(__file__).resolve().parents[2] / "data"]
    roots.extend(
        c.artifact_root
        if c.artifact_root.is_absolute()
        else Path(workspace) / c.artifact_root
        for c in adapter.courses
    )
    if any(
        path.resolve().is_relative_to(root.resolve())
        or root.resolve().is_relative_to(path.resolve())
        for root in roots
    ):
        raise ValueError("Index output must be separate from source/artifact roots")
    return path


class VectorArtifact(Contract):
    schema_version: Literal[1] = 1
    plan_id: Hash
    embedding_version: Hash
    vectors: tuple[tuple[float, ...], ...]

    @property
    def artifact_id(self):
        return fingerprint(self.model_dump(mode="json"))


def validate_vectors(artifact, plan):
    artifact = VectorArtifact.model_validate_json(artifact.model_dump_json())
    if (
        artifact.plan_id != plan.plan_id
        or artifact.embedding_version != plan.collection.embedding.version
    ):
        raise ValueError("Vector artifact plan/model conflict")
    checked_vectors(artifact.vectors, plan.collection.embedding, len(plan.units))
    return artifact


def embed_plan(plan, adapter, embedder, *, workspace, destination=None):
    plan = IngestionPlan.model_validate_json(plan.model_dump_json())
    revalidate_plan(plan, adapter, workspace=workspace)
    if embedder.config != plan.collection.embedding:
        raise ValueError("Embedding configuration conflict")
    path = (
        checked_artifact_path(destination, adapter, workspace)
        if destination is not None
        else None
    )
    if path is not None and path.exists():
        return validate_vectors(
            VectorArtifact.model_validate_json(path.read_bytes()), plan
        )
    vectors = []
    size = embedder.config.batch_size
    for i in range(0, len(plan.units), size):
        revalidate_plan(
            plan,
            adapter,
            workspace=workspace,
            source_ids={p.source_id for p in plan.units[i : i + size]},
        )
        vectors.extend(embedder.encode([p.text for p in plan.units[i : i + size]]))
    artifact = validate_vectors(
        VectorArtifact(
            plan_id=plan.plan_id,
            embedding_version=embedder.config.version,
            vectors=tuple(tuple(v) for v in vectors),
        ),
        plan,
    )
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(path, artifact.model_dump(mode="json"))
    revalidate_plan(plan, adapter, workspace=workspace)
    return artifact


@contextmanager
def index_lock(directory):
    directory = Path(directory).absolute()
    if any(p.is_symlink() for p in (directory, *directory.parents)):
        raise ValueError("Symlink index state root forbidden")
    directory.mkdir(parents=True, exist_ok=True)
    fd = os.open(
        directory / "index.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield directory
    finally:
        os.close(fd)


def all_points(client, contract):
    check_collection(client, contract)
    points, offset = [], None
    while True:
        batch, offset = client.scroll(
            contract.name,
            limit=128,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        points.extend(batch)
        if offset is None:
            return points


def checked_existing(client, plan, artifact):
    expected = {
        p.point_id: (p, v) for p, v in zip(plan.units, artifact.vectors, strict=True)
    }
    selected = {s.input["source_id"] for s in plan.sources}
    slots = {
        (s.input["course_id"], s.input["section_key"]): (
            s.input["lecture_id"],
            s.input["resource_id"],
            s.input["source_id"],
        )
        for s in plan.sources
    }
    matched = set()
    for record in all_points(client, plan.collection):
        if record.payload is None or any(
            key not in record.payload for key in plan.collection.required_payload_fields
        ):
            raise ValueError(
                "Missing explicit required payload fields/version; never infer defaults"
            )
        payload = TranscriptPayload.model_validate(record.payload)
        payload.check_collection(plan.collection)
        if str(record.id) != payload.point_id:
            raise ValueError("Foreign point ID/payload conflict")
        checked_vectors([record.vector], plan.collection.embedding, 1)
        slot = slots.get((payload.course_id, payload.section_key))
        if slot is not None and slot != (
            payload.lecture_id,
            payload.resource_id,
            payload.source_id,
        ):
            raise ValueError(
                "Replaced source in selected lecture; old points require an explicit new index"
            )
        if payload.source_id not in selected:
            continue
        if payload.point_id not in expected:
            raise ValueError(
                "Stale source/chunkplan detected; create a new index, never delete implicitly"
            )
        target, vector = expected[payload.point_id]
        if payload != target or not all(
            math.isclose(a, b, abs_tol=1e-6, rel_tol=1e-5)
            for a, b in zip(record.vector, vector, strict=True)
        ):
            raise ValueError("Existing point payload/vector conflict")
        matched.add(payload.point_id)
    return matched


class UploadState(Contract):
    schema_version: Literal[1] = 1
    plan_id: Hash
    artifact_id: Hash
    status: Literal["uploading", "failed", "done"]
    expected_points: int = Field(ge=1)
    verified_points: int = Field(default=0, ge=0)
    error_class: str | None = None

    @model_validator(mode="after")
    def completion(self):
        if self.verified_points > self.expected_points or (
            self.status == "done"
            and (
                self.verified_points != self.expected_points
                or self.error_class is not None
            )
        ):
            raise ValueError("Invalid completion counts/error state")
        return self


def upsert_plan(
    client,
    plan,
    artifact,
    adapter,
    *,
    workspace,
    state_root,
    execute=False,
    allow_create=False,
    batch_size=32,
):
    plan = IngestionPlan.model_validate_json(plan.model_dump_json())
    artifact = validate_vectors(artifact, plan)
    revalidate_plan(plan, adapter, workspace=workspace)
    if not execute:
        return {
            "dry_run": True,
            "plan_id": plan.plan_id,
            "expected_points": len(plan.units),
        }
    if not 1 <= batch_size <= 256:
        raise ValueError("Invalid upload batch size")
    from qdrant_client.models import PointStruct

    state_root = checked_artifact_path(state_root, adapter, workspace)
    with index_lock(state_root / plan.collection.name) as directory:
        receipt = directory / (plan.plan_id + ".json")
        if receipt.exists():
            prior = UploadState.model_validate_json(receipt.read_bytes())
            if (
                prior.plan_id != plan.plan_id
                or prior.artifact_id != artifact.artifact_id
                or prior.expected_points != len(plan.units)
            ):
                raise ValueError("Upload receipt identity/hash conflict")

        def save(status, count, error=None):
            value = UploadState(
                plan_id=plan.plan_id,
                artifact_id=artifact.artifact_id,
                status=status,
                expected_points=len(plan.units),
                verified_points=count,
                error_class=error,
            )
            atomic_json(
                receipt, value.model_dump(mode="json"), replace=receipt.exists()
            )
            return value

        count = 0
        try:
            ensure_collection(client, plan.collection, allow_create=allow_create)
            matched = checked_existing(client, plan, artifact)
            count = len(matched)
            save("uploading", count)
            pending = [
                (p, v)
                for p, v in zip(plan.units, artifact.vectors, strict=True)
                if p.point_id not in matched
            ]
            for i in range(0, len(pending), batch_size):
                revalidate_plan(
                    plan,
                    adapter,
                    workspace=workspace,
                    source_ids={p.source_id for p, _ in pending[i : i + batch_size]},
                )
                check_collection(client, plan.collection)
                batch = pending[i : i + batch_size]
                client.upsert(
                    plan.collection.name,
                    points=[
                        PointStruct(
                            id=p.point_id,
                            vector=list(v),
                            payload=p.model_dump(mode="json"),
                        )
                        for p, v in batch
                    ],
                    wait=True,
                )
                matched = checked_existing(client, plan, artifact)
                count = len(matched)
                save("uploading", count)
            matched = checked_existing(client, plan, artifact)
            if len(matched) != len(plan.units):
                raise ValueError("Upload acknowledged but expected points missing")
            revalidate_plan(plan, adapter, workspace=workspace)
            return save("done", len(matched))
        except Exception as error:
            save("failed", count, type(error).__name__)
            raise
