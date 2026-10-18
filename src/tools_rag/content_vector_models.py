"""ContentRecord vectors, deliberately incompatible with timed TranscriptPayload."""

from typing import Literal
from uuid import UUID, uuid5

from pydantic import Field, model_validator

from src.content_store.index_models import _Versioned
from src.content_store.models import Name, fingerprint, sha256
from src.job_control.models import Sha
from src.model_discovery.cs50_index import EmbeddingConfig
from src.tools_rag.cs50_ingestion import VectorArtifact

NAMESPACE = UUID("8c17f710-6b6c-5edc-a6d3-c9f545229a62")
FILTERS = (
    "source_id",
    "source_version_id",
    "parsed_version_id",
    "generation_id",
    "index_record_id",
    "collection_contract_id",
)


class ContentVectorConfig(_Versioned):
    schema_version: Literal[1]
    name: str = Field(pattern=r"^content_[a-z0-9_]{1,40}$")
    embedding: EmbeddingConfig
    backend_set: Literal["vector"] = "vector"
    adapter_version: Literal["content_vector_adapter_v1"] = "content_vector_adapter_v1"
    payload_schema: Literal["content_vector_payload_v1"] = "content_vector_payload_v1"
    distance: Literal["Cosine"] = "Cosine"
    filter_indexes: tuple[str, ...] = FILTERS

    @model_validator(mode="before")
    @classmethod
    def explicit_embedding(cls, value):
        if isinstance(value, dict) and isinstance(value.get("embedding"), dict):
            e = value["embedding"]
            if type(e.get("schema_version")) is not int or e["schema_version"] != 1:
                raise ValueError("explicit embedding schema required")
        return value

    @model_validator(mode="after")
    def exact(self):
        if self.filter_indexes != FILTERS:
            raise ValueError("exact ContentRecord filters required")
        return self

    @property
    def contract_id(self):
        return fingerprint(self.model_dump(mode="json"))


class ContentCollection(ContentVectorConfig):
    name: str = Field(pattern=r"^content_[a-z0-9_]{1,80}$")
    source_id: Name
    generation_id: str = Field(pattern=r"^content_index_generation_v1:[0-9a-f]{64}$")
    payload_schema_sha256: Sha

    @model_validator(mode="after")
    def schema(self):
        if self.payload_schema_sha256 != fingerprint(
            ContentVectorPayload.model_json_schema()
        ):
            raise ValueError("ContentRecord schema conflict")
        return self


class ContentVectorPayload(_Versioned):
    schema_version: Literal[1]
    adapter_version: Literal["content_vector_adapter_v1"]
    payload_schema: Literal["content_vector_payload_v1"]
    index_record_id: Name
    source_id: Name
    source_version_id: Name
    parsed_version_id: Name
    block_id: Name
    record_start: int = Field(strict=True, ge=0)
    record_end: int = Field(strict=True, gt=0)
    child_start: int = Field(strict=True, ge=0)
    child_end: int = Field(strict=True, gt=0)
    offset_unit: Literal["unicode_codepoint"]
    text_sha256: Sha
    child_text: str = Field(min_length=1, max_length=2000)
    child_text_sha256: Sha
    projection_fingerprint: Sha
    payload_sha256: Sha
    embedding_model: str
    embedding_revision: str
    embedding_config_fingerprint: Sha
    collection_name: str = Field(pattern=r"^content_[a-z0-9_]{1,80}$")
    collection_contract_id: Sha
    generation_id: str = Field(pattern=r"^content_index_generation_v1:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def anchor(self):
        if (
            not (
                self.record_start
                <= self.child_start
                < self.child_end
                <= self.record_end
            )
            or len(self.child_text) != self.child_end - self.child_start
            or sha256(self.child_text.encode()) != self.child_text_sha256
        ):
            raise ValueError("child anchor/hash conflict")
        return self

    @property
    def point_id(self):
        return str(uuid5(NAMESPACE, fingerprint(self.model_dump(mode="json"))))


class ContentVectorPlan(_Versioned):
    schema_version: Literal[1]
    collection: ContentCollection
    record_set_sha256: Sha
    units: tuple[ContentVectorPayload, ...] = Field(max_length=4096)

    @model_validator(mode="after")
    def bound(self):
        if len({p.point_id for p in self.units}) != len(self.units):
            raise ValueError("duplicate vector point")
        for p in self.units:
            if (
                p.source_id,
                p.generation_id,
                p.collection_name,
                p.collection_contract_id,
                p.embedding_model,
                p.embedding_revision,
                p.embedding_config_fingerprint,
            ) != (
                self.collection.source_id,
                self.collection.generation_id,
                self.collection.name,
                self.collection.contract_id,
                self.collection.embedding.model,
                self.collection.embedding.revision,
                self.collection.embedding.version,
            ):
                raise ValueError("point collection/model conflict")
        return self

    @property
    def plan_id(self):
        return fingerprint(self.model_dump(mode="json"))


class VectorPartition(_Versioned):
    schema_version: Literal[1]
    plan: ContentVectorPlan
    artifact: VectorArtifact
    artifact_id: Sha

    @model_validator(mode="before")
    @classmethod
    def explicit_artifact(cls, value):
        if isinstance(value, dict) and isinstance(value.get("artifact"), dict):
            a = value["artifact"]
            if type(a.get("schema_version")) is not int or a["schema_version"] != 1:
                raise ValueError("explicit vector artifact schema required")
        return value

    @model_validator(mode="after")
    def artifact_binding(self):
        if (
            self.artifact.artifact_id != self.artifact_id
            or self.artifact.plan_id != self.plan.plan_id
        ):
            raise ValueError("vector artifact identity conflict")
        return self


class HybridContract(_Versioned):
    """Preparation only; no active hybrid generation in A."""

    schema_version: Literal[1]
    backend_set: Literal["lexical+vector"] = "lexical+vector"
    ranking_schema: Literal["backend_rrf_v1"] = "backend_rrf_v1"
    rank_constant: Literal[60] = 60
    activation: Literal["blocked_pending_pilot"] = "blocked_pending_pilot"
