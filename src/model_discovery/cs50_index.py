"""Derived transcript index contracts; no embedding/DB SDK import or source mutation."""

from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID, uuid5

from pydantic import Field, model_validator

from src.tools_knowledge.cs50_checkpoint import Contract, fingerprint

Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Name = Annotated[str, Field(min_length=1, pattern=r"\S")]
NAMESPACE = UUID("428d0c9d-1dd6-5cfb-b218-b82bf9d11a70")


class EmbeddingConfig(Contract):
    schema_version: Literal[1] = 1
    provider: Literal["local", "fake"] = "local"
    model: Name = "intfloat/multilingual-e5-base"
    revision: Name
    dimension: int = Field(default=768, ge=2, le=4096)
    max_tokens: int = Field(default=512, ge=8, le=8192)
    normalization: Literal["l2"] = "l2"
    query_prefix: str = "query: "
    passage_prefix: str = "passage: "
    preprocessing: Literal["original_text_v1"] = "original_text_v1"
    segmentation: Literal["offset_windows_v1"] = "offset_windows_v1"
    batch_size: int = Field(default=16, ge=1, le=128)

    @model_validator(mode="after")
    def known_model_contract(self):
        if self.provider == "fake":
            if self.model != "cs50-test-hash" or self.revision != "fake-v1":
                raise ValueError("Fake vectors must never claim a real embedding model")
        elif self.model == "intfloat/multilingual-e5-base":
            if (
                self.dimension,
                self.max_tokens,
                self.query_prefix,
                self.passage_prefix,
            ) != (768, 512, "query: ", "passage: "):
                raise ValueError(
                    "E5 requires 768 dimensions, 512 tokens and query/passage prefixes"
                )
        elif self.model == "sentence-transformers/all-MiniLM-L6-v2":
            if (
                self.dimension,
                self.max_tokens,
                self.query_prefix,
                self.passage_prefix,
            ) != (384, 256, "", ""):
                raise ValueError(
                    "MiniLM contract requires 384 dimensions / 256 tokens / no prefixes"
                )
        else:
            raise ValueError(
                "Unsupported local model; introduce an explicit versioned contract"
            )
        if self.provider == "local":
            import re

            if not re.fullmatch(r"[0-9a-f]{40}", self.revision):
                raise ValueError(
                    "Local embeddings require an immutable model commit revision"
                )
        return self

    @property
    def version(self):
        return fingerprint(self.model_dump(mode="json"))

    @classmethod
    def fake(cls, *, dimension=16, max_tokens=32):
        return cls(
            provider="fake",
            model="cs50-test-hash",
            revision="fake-v1",
            dimension=dimension,
            max_tokens=max_tokens,
            query_prefix="",
            passage_prefix="",
        )


class CollectionContract(Contract):
    schema_version: Literal[1] = 1
    name: str = Field(
        default="cs50_transcript_chunks_v1", pattern=r"^[a-z][a-z0-9_]{2,100}$"
    )
    distance: Literal["Cosine"] = "Cosine"
    embedding: EmbeddingConfig
    ingestion_schema_version: Literal[1] = 1
    payload_schema: Literal["cs50_transcript_payload_v1"] = "cs50_transcript_payload_v1"
    filter_indexes: tuple[
        Literal["course_id", "lecture_id", "source_id", "language"], ...
    ] = ("course_id", "lecture_id", "source_id", "language")

    @model_validator(mode="after")
    def all_indexes(self):
        if (
            set(self.filter_indexes)
            != {"course_id", "lecture_id", "source_id", "language"}
            or len(self.filter_indexes) != 4
        ):
            raise ValueError("Exactly four required keyword filter indexes")
        return self

    @property
    def contract_id(self):
        return fingerprint(self.model_dump(mode="json"))


class TranscriptPayload(Contract):
    ingestion_schema_version: Literal[1] = 1
    course_id: Name
    section_key: Name
    lecture_id: Name
    resource_id: Name
    source_id: Name
    media_id: str | None = None
    chunk_id: Name
    language: Literal["en"] = "en"
    original_url: str
    raw_sha256: Hash
    transcript_sha256: Hash
    receipt_sha256: Hash
    input_binding_sha256: Hash
    chunk_plan_sha256: Hash
    chunking: dict
    transcript_provenance: dict
    provenance_sha256: Hash
    discovery_provenance: tuple[dict, ...]
    original_chunk_text: Name
    original_chunk_segment_ids: tuple[int, ...]
    original_chunk_start: float = Field(ge=0, allow_inf_nan=False)
    original_chunk_end: float = Field(ge=0, allow_inf_nan=False)
    text: Name
    segment_ids: tuple[int, ...]
    start: float = Field(ge=0, allow_inf_nan=False)
    end: float = Field(ge=0, allow_inf_nan=False)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    unit_index: int = Field(ge=0)
    unit_count: int = Field(ge=1)
    embedding_model: Name
    embedding_version: Hash
    collection_contract_id: Hash
    source_origin: Literal["official", "synthetic"]

    @model_validator(mode="after")
    def consistent_unit(self):
        u = urlsplit(self.original_url)
        if (
            u.scheme != "https"
            or u.hostname != "cdn.cs50.net"
            or u.username
            or u.password
            or u.query
            or u.fragment
        ):
            raise ValueError("Expected explicit official credential-free HTTPS SRT URL")
        if (
            self.char_end > len(self.original_chunk_text)
            or self.char_start >= self.char_end
        ):
            raise ValueError("Invalid original-text offsets")
        if self.text != self.original_chunk_text[self.char_start : self.char_end]:
            raise ValueError("Embedding text must equal the original chunk substring")
        if not self.segment_ids or len(set(self.segment_ids)) != len(self.segment_ids):
            raise ValueError("Nonempty unique segment references required")
        if not set(self.segment_ids).issubset(self.original_chunk_segment_ids):
            raise ValueError("Embedding segment references outside original chunk")
        if not (
            self.original_chunk_start
            <= self.start
            <= self.end
            <= self.original_chunk_end
        ):
            raise ValueError("Times must remain within original chunk")
        if self.unit_index >= self.unit_count:
            raise ValueError("Invalid embedding unit order")
        provenance = self.transcript_provenance
        if (
            provenance.get("source_url") != self.original_url
            or provenance.get("language") != self.language
            or provenance.get("transcript_source") != "official_subtitle"
            or provenance.get("media_format") != "srt"
            or provenance.get("media_id") != self.media_id
        ):
            raise ValueError("Transcript provenance conflicts with source identity")
        source_file = provenance.get("source_file")
        if source_file is not None and (
            source_file.startswith(("/", "\\")) or ":" in source_file
        ):
            raise ValueError("Absolute source paths forbidden in index payload")
        return self

    @property
    def point_id(self):
        return str(
            uuid5(
                NAMESPACE,
                fingerprint(
                    {
                        "schema": 1,
                        "contract": self.collection_contract_id,
                        "source": self.source_id,
                        "transcript": self.transcript_sha256,
                        "chunk_plan": self.chunk_plan_sha256,
                        "chunk": self.chunk_id,
                        "unit": self.unit_index,
                        "offsets": [self.char_start, self.char_end],
                    }
                ),
            )
        )

    def check_collection(self, contract):
        if (
            self.collection_contract_id,
            self.embedding_model,
            self.embedding_version,
        ) != (
            contract.contract_id,
            contract.embedding.model,
            contract.embedding.version,
        ):
            raise ValueError("Point embedding/collection identity mismatch")
