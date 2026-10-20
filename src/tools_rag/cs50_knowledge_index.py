"""Read-only future Knowledge collection mapping. No DB/LLM execution path."""

from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID, uuid5

from pydantic import Field, model_validator

from src.model_discovery.cs50_index import EmbeddingConfig, Hash, Name
from src.tools_knowledge.cs50_checkpoint import Contract, fingerprint
from src.tools_rag.cs50_embeddings import source_time_window
from src.tools_rag.cs50_ingestion import revalidate_plan

KNOWLEDGE_NAMESPACE = UUID("723a8e2b-0cb8-5d3d-b12d-6bb4d7d741a0")


class KnowledgeCollectionDefinition(Contract):
    schema_version: Literal[1] = 1
    name: Literal["cs50_knowledge_items_v1"] = "cs50_knowledge_items_v1"
    embedding: EmbeddingConfig
    distance: Literal["Cosine"] = "Cosine"
    payload_schema: Literal["cs50_knowledge_item_v1"] = "cs50_knowledge_item_v1"
    execution_supported: Literal[False] = False
    required_fields: tuple[str, ...] = (
        "source_id",
        "course_id",
        "lecture_id",
        "original_knowledge_id",
        "evidence",
        "kind",
        "topics",
        "quality_status",
        "extraction_model",
        "prompt_version",
        "result_content_sha256",
        "transcript_sha256",
    )


class KnowledgeMappingContext(Contract):
    extraction_provider: str | None = None
    extraction_model: str | None = None
    prompt_version: str | None = None
    result_schema_version: str | None = None
    result_file_sha256: Hash | None = None
    extraction_receipt_sha256: Hash | None = None
    quality_status: Literal["unreviewed", "synthetic", "reviewed"] = "unreviewed"
    review_reference: str | None = None
    execution_mode: Literal["offline", "llm"] | None = None

    @model_validator(mode="after")
    def review(self):
        if self.extraction_provider == "fake" and self.quality_status != "synthetic":
            raise ValueError("Fake extraction must remain explicitly synthetic")
        if self.quality_status == "reviewed" and not self.review_reference:
            raise ValueError("Reviewed quality needs explicit human review provenance")
        if self.review_reference and self.review_reference.startswith(
            ("/", "\\", "file:")
        ):
            raise ValueError("Review reference must not expose a machine file path")
        if self.review_reference and "://" in self.review_reference:
            url = urlsplit(self.review_reference)
            if url.scheme != "https" or url.username or url.password or url.query:
                raise ValueError("Review URI must not expose credentials or tokens")
        return self


class KnowledgeIndexItem(Contract):
    schema_version: Literal[1] = 1
    course_id: Name
    section_key: Name
    lecture_id: Name
    resource_id: Name
    source_id: Name
    media_id: str | None
    original_url: Name
    transcript_sha256: Hash
    raw_sha256: Hash
    chunk_plan_sha256: Hash
    transcript_provenance: dict
    kind: Literal["statement", "formula"]
    original_knowledge_id: Name
    text: Name
    latex: str | None = None
    semantic_type: Name
    topics: tuple[str, ...]
    evidence: tuple[dict, ...] = Field(min_length=1)
    result_content_sha256: Hash
    context: KnowledgeMappingContext
    quality_status: Literal["unreviewed", "synthetic", "reviewed"]
    extraction_provider: str | None
    extraction_model: str | None
    prompt_version: str | None
    result_schema_version: str | None
    extraction_context_verified: bool
    missing_original_metadata: tuple[str, ...]
    visual_provenance_complete: Literal[False] = False
    original_item: dict

    @model_validator(mode="after")
    def metadata(self):
        if any(
            getattr(self, key) != getattr(self.context, key)
            for key in (
                "quality_status",
                "extraction_provider",
                "extraction_model",
                "prompt_version",
                "result_schema_version",
            )
        ):
            raise ValueError("Knowledge result/context metadata conflict")
        return self

    @property
    def point_id(self):
        return str(
            uuid5(
                KNOWLEDGE_NAMESPACE,
                fingerprint(
                    {
                        "schema": 1,
                        "source": self.source_id,
                        "result": self.result_content_sha256,
                        "kind": self.kind,
                        "item": self.original_knowledge_id,
                        "evidence": self.evidence,
                    }
                ),
            )
        )


def map_knowledge_document(
    document,
    plan,
    adapter,
    context,
    *,
    workspace,
    result_file=None,
    extraction_receipt=None,
):
    """Preserve actual models/items and checked original references; never upload."""
    revalidate_plan(plan, adapter, workspace=workspace)
    from src.model_knowledge.data_knowledge import (
        ConsolidatedKnowledgeDocument,
        TranscriptKnowledgeDocument,
    )

    if isinstance(document, TranscriptKnowledgeDocument):
        document = TranscriptKnowledgeDocument.model_validate_json(
            document.model_dump_json()
        )
    elif isinstance(document, ConsolidatedKnowledgeDocument):
        document = ConsolidatedKnowledgeDocument.model_validate_json(
            document.model_dump_json()
        )
    else:
        raise ValueError(
            "Explicit extraction or deterministic consolidation model required"
        )
    context = KnowledgeMappingContext.model_validate(context.model_dump())
    sources = [s for s in plan.sources if s.input["source_id"] == document.source_id]
    if len(sources) != 1:
        raise ValueError("Knowledge source_id missing/foreign; never infer identity")
    source = sources[0]
    reference = source.units[0]
    from src.tools_lecture.execute_cs50 import digest

    def read_proof(path):
        path = Path(path).absolute()
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("Symlink Knowledge proof forbidden")
        return path

    if context.result_file_sha256 is not None:
        if result_file is None:
            raise ValueError(
                "Claimed result file hash requires its explicit original artifact"
            )
        path = read_proof(result_file)
        if (
            digest(path) != context.result_file_sha256
            or type(document).model_validate_json(path.read_bytes()) != document
        ):
            raise ValueError("Knowledge result file hash/content conflict")
    proof_verified = False
    if context.extraction_receipt_sha256 is not None:
        from src.tools_knowledge.cs50_checkpoint import JobCheckpoint

        if extraction_receipt is None:
            raise ValueError("Claimed extraction receipt hash requires explicit proof")
        path = read_proof(extraction_receipt)
        if digest(path) != context.extraction_receipt_sha256:
            raise ValueError("Extraction receipt hash conflict")
        receipt = JobCheckpoint.model_validate_json(path.read_bytes())
        identity = receipt.identity
        if (
            receipt.status != "done"
            or any(
                getattr(identity, key) != getattr(reference, key)
                for key in (
                    "source_id",
                    "course_id",
                    "lecture_id",
                    "raw_sha256",
                    "transcript_sha256",
                    "chunk_plan_sha256",
                )
            )
            or identity.input_binding_sha256 != fingerprint(source.input)
        ):
            raise ValueError("Extraction receipt source/completion conflict")
        if identity.execution_mode != "llm" and context.quality_status != "synthetic":
            raise ValueError("Offline extraction receipt must remain synthetic")
        values = context.model_dump(mode="json")
        for key, value in (
            ("extraction_provider", identity.provider),
            ("extraction_model", identity.model),
            ("prompt_version", identity.prompt_version),
            ("result_schema_version", identity.result_schema_version),
        ):
            if getattr(context, key) is not None and getattr(context, key) != value:
                raise ValueError(
                    "Declared extraction metadata conflicts with actual receipt"
                )
            values[key] = value
        if (
            context.execution_mode is not None
            and context.execution_mode != identity.execution_mode
        ):
            raise ValueError("Extraction execution-mode conflict")
        values["execution_mode"] = identity.execution_mode
        context = KnowledgeMappingContext.model_validate(values)
        from src.model_knowledge.data_knowledge import ChunkKnowledgeResult
        from src.tools_knowledge.cs50_checkpoint import ARTIFACTS

        results = {}
        for chunk_id, state in receipt.chunks.items():
            directory = path.parent / fingerprint(chunk_id)
            for key, filename in ARTIFACTS.items():
                artifact_path = read_proof(directory / filename)
                if digest(artifact_path) != state.artifacts[key]:
                    raise ValueError("Extraction receipt artifact hash conflict")
            result = ChunkKnowledgeResult.model_validate_json(
                (directory / ARTIFACTS["result"]).read_bytes()
            )
            if result.analysis.chunk_id != chunk_id:
                raise ValueError("Extraction receipt artifact chunk conflict")
            results[chunk_id] = result
        if isinstance(document, TranscriptKnowledgeDocument):
            if {c.analysis.chunk_id for c in document.chunks} != set(results) or any(
                c != results[c.analysis.chunk_id] for c in document.chunks
            ):
                raise ValueError("Extraction document does not match receipt artifacts")
        else:
            original_ids = {
                cid: {item.statement_id for item in r.extraction.statements}
                | {item.expression_id for item in r.extraction.formulas}
                if r.extraction
                else set()
                for cid, r in results.items()
            }
            if any(
                e.item_id not in original_ids.get(e.chunk_id, set())
                for item in (*document.statements, *document.formulas)
                for e in item.evidence
            ):
                raise ValueError(
                    "Consolidated item references foreign extraction artifacts"
                )
        proof_verified = True
    for key in ("course_id", "lecture_id", "language", "media_id"):
        value = getattr(document, key, None)
        if value is not None and value != getattr(reference, key):
            raise ValueError("Knowledge metadata conflicts with verified source")
    if (
        document.transcript_url is not None
        and document.transcript_url != reference.original_url
    ):
        raise ValueError("Knowledge URL conflicts with verified source")
    if (
        document.transcript_provenance is not None
        and fingerprint(document.transcript_provenance.model_dump(mode="json"))
        != reference.provenance_sha256
    ):
        raise ValueError("Knowledge transcript provenance conflict")
    if reference.source_origin == "synthetic" and context.quality_status != "synthetic":
        raise ValueError("Synthetic source cannot acquire an unmarked quality status")
    chunks = {p.chunk_id: p for p in source.units}
    from src.tools_knowledge.bind_cs50_transcript import (
        CS50PortableInput,
        load_knowledge_transcript,
    )

    transcript = load_knowledge_transcript(
        adapter, CS50PortableInput.model_validate(source.input), workspace=workspace
    )
    original_segments = {s.seg_id: s for s in transcript.segments if s.text.strip()}
    items = []
    result_hash = fingerprint(document.model_dump(mode="json"))
    missing = tuple(
        k
        for k in (
            "course_id",
            "lecture_id",
            "language",
            "transcript_provenance",
            "transcript_url",
            "media_id",
        )
        if getattr(document, k, None) is None
    )

    def mapped(item, kind, evidences, topic_context=()):
        for evidence in evidences:
            chunk = chunks.get(evidence["chunk_id"])
            if chunk is None or evidence["source"] not in (
                "transcript",
                "transcript+visual",
            ):
                raise ValueError("Unresolved chunk/visual-only source proof")
            if not evidence["segment_ids"] or not set(evidence["segment_ids"]).issubset(
                chunk.original_chunk_segment_ids
            ):
                raise ValueError("Missing/foreign evidence segment references")
            if (
                not chunk.original_chunk_start
                <= evidence["start"]
                <= evidence["end"]
                <= chunk.original_chunk_end
            ):
                raise ValueError("Evidence times outside actual original chunk")
            cues = [original_segments[sid] for sid in evidence["segment_ids"]]
            actual_times = {
                source_time_window(cues),
                (chunk.original_chunk_start, chunk.original_chunk_end),
            }
            if (evidence["start"], evidence["end"]) not in actual_times:
                raise ValueError("Evidence times are not original cue/chunk timestamps")
        identifier = item.statement_id if kind == "statement" else item.expression_id
        return KnowledgeIndexItem(
            **{
                k: getattr(reference, k)
                for k in (
                    "course_id",
                    "section_key",
                    "lecture_id",
                    "resource_id",
                    "source_id",
                    "media_id",
                    "original_url",
                    "transcript_sha256",
                    "raw_sha256",
                    "chunk_plan_sha256",
                    "transcript_provenance",
                )
            },
            kind=kind,
            original_knowledge_id=identifier,
            text=item.text if kind == "statement" else item.plain_text or item.latex,
            latex=getattr(item, "latex", None),
            semantic_type=(
                item.semantic_type if kind == "statement" else item.expression_type
            ).value,
            topics=tuple(
                dict.fromkeys(
                    ((item.topic,) if getattr(item, "topic", None) else ())
                    + tuple(topic_context)
                )
            ),
            evidence=tuple(evidences),
            result_content_sha256=result_hash,
            context=context,
            missing_original_metadata=missing,
            original_item=item.model_dump(mode="json"),
            extraction_context_verified=proof_verified,
            **{
                key: getattr(context, key)
                for key in (
                    "quality_status",
                    "extraction_provider",
                    "extraction_model",
                    "prompt_version",
                    "result_schema_version",
                )
            },
        )

    if isinstance(document, TranscriptKnowledgeDocument):
        for chunk in document.chunks:
            if chunk.extraction is None:
                continue
            if chunk.extraction.chunk_id != chunk.analysis.chunk_id:
                raise ValueError("Extraction/analysis chunk identity conflict")
            for kind, group in (
                ("statement", chunk.extraction.statements),
                ("formula", chunk.extraction.formulas),
            ):
                for item in group:
                    evidence = {
                        k: getattr(item, k)
                        for k in (
                            "segment_ids",
                            "start",
                            "end",
                            "source",
                            "llm_confidence",
                        )
                    }
                    evidence |= {
                        "chunk_id": chunk.extraction.chunk_id,
                        "item_id": item.statement_id
                        if kind == "statement"
                        else item.expression_id,
                    }
                    items.append(
                        mapped(
                            item,
                            kind,
                            [evidence],
                            (chunk.analysis.topic,) if chunk.analysis.topic else (),
                        )
                    )
    else:
        for kind, group in (
            ("statement", document.statements),
            ("formula", document.formulas),
        ):
            for item in group:
                if not item.evidence:
                    raise ValueError("Knowledge items need actual evidence")
                items.append(
                    mapped(
                        item,
                        kind,
                        [e.model_dump(mode="json") for e in item.evidence],
                        document.topics,
                    )
                )
    if len({i.point_id for i in items}) != len(items):
        raise ValueError("Duplicate Knowledge identity")
    return tuple(items)
