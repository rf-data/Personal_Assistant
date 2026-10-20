"""Workflow envelopes around the authoritative C23/C24 gold contracts."""

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, JsonValue, model_validator

from src.content_store.artifacts import explicit_root
from src.content_store.models import ContentLocator, Name
from src.content_store.read_models import ContentReadSettings
from src.job_control.models import Identifier, Principal, Sha
from src.model_evaluation.content_retrieval import (
    IndependentReview,
    RetrievalConfiguration,
    RetrievalResults,
    Versioned,
)
from src.model_evaluation.material_evaluation import Dimension
from src.tools_rag.content_index_models import IndexSelection, VersionBinding

Permission = Literal[
    "read", "manage", "annotate", "confirm", "pool", "export", "report", "accept"
]


class ReviewGrant(Versioned):
    subject: Identifier
    dataset_id: Identifier
    source_ids: tuple[Name, ...] = Field(min_length=1, max_length=16)
    permissions: tuple[Permission, ...] = Field(min_length=1, max_length=8)


class ReviewSettings(Versioned):
    root: Path
    content: ContentReadSettings
    writes_enabled: bool = Field(default=False, strict=True)
    real_reviews_enabled: bool = Field(default=False, strict=True)
    owner_authorization_reference: Name | None = None
    grants: tuple[ReviewGrant, ...] = Field(default=(), max_length=128)

    @model_validator(mode="after")
    def roots(self):
        explicit_root(self.root)
        if (
            self.root.is_relative_to(self.content.root)
            or self.content.root.is_relative_to(self.root)
            or self.content.cursor_key_file.is_relative_to(self.root)
        ):
            raise ValueError("separate review and content roots required")
        keys = [(g.subject, g.dataset_id) for g in self.grants]
        if len(keys) != len(set(keys)):
            raise ValueError("one explicit grant per subject/dataset required")
        if self.real_reviews_enabled and not self.owner_authorization_reference:
            raise ValueError("real review authorization reference required")
        return self


class QuerySpec(Versioned):
    query_id: Identifier
    text: str = Field(min_length=1, max_length=512)


class DatasetSpec(Versioned):
    dataset_id: Identifier
    dataset_version: str = Field(min_length=1, max_length=80)
    selection: IndexSelection
    retrieval: RetrievalConfiguration
    queries: tuple[QuerySpec, ...] = Field(min_length=1, max_length=16)
    corpus_reference: Name

    @model_validator(mode="after")
    def bounded(self):
        if not 1 <= len(self.selection.parsed_version_ids) <= 16:
            raise ValueError("one to sixteen versions required")
        if len({q.query_id for q in self.queries}) != len(self.queries):
            raise ValueError("unique queries required")
        return self


class DatasetBinding(Versioned):
    spec: DatasetSpec
    actor: Principal
    versions: tuple[VersionBinding, ...]
    origin: Literal["synthetic", "real"]


class Region(Versioned):
    source_id: Name
    source_version_id: Name
    parsed_version_id: Name
    block_id: Name
    text_sha256: Sha
    raw_sha256: Sha
    parser_config_id: Name
    payload_sha256: Sha
    projection_sha256: Sha
    locator: ContentLocator
    start: int = Field(strict=True, ge=0)
    end: int = Field(strict=True, ge=1)
    original_region: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def interval(self):
        if self.end - self.start != len(self.original_region):
            raise ValueError("exact Unicode codepoint interval required")
        if self.raw_sha256 != self.locator.raw_artifact_sha256:
            raise ValueError("raw locator mismatch")
        return self


class TaskSpec(Versioned):
    task_id: Identifier
    kind: Literal["parsing", "retrieval"]
    assignee: Identifier
    region: Region
    query_id: Identifier | None = None
    dimension: Dimension = "text"
    unanchored_finding: bool = Field(default=False, strict=True)
    corpus_entry_id: Identifier | None = None

    @model_validator(mode="after")
    def query(self):
        if (self.kind == "retrieval") != (self.query_id is not None):
            raise ValueError("query required only for retrieval")
        if self.unanchored_finding and self.kind != "parsing":
            raise ValueError("unanchored observations are parsing findings only")
        if self.kind == "parsing" and self.corpus_entry_id is None:
            raise ValueError("explicit C23 corpus entry identity required")
        if self.kind == "retrieval" and self.corpus_entry_id is not None:
            raise ValueError("C23 corpus entry applies only to parsing")
        return self


class Annotation(Versioned):
    mode: Literal["independent_original", "assisted"]
    grade: int | None = Field(default=None, strict=True, ge=0, le=3)
    quality: Literal["correct", "partial", "incorrect", "undetermined"] | None = None
    expected_content: str | None = Field(default=None, max_length=2000)
    error_categories: tuple[Identifier, ...] = Field(default=(), max_length=16)
    comment: str = Field(min_length=1, max_length=1000)


class Mutation(Versioned):
    expected_revision: Sha | None
    idempotency_key: Identifier
    reason: str = Field(min_length=1, max_length=500)


class CreateDataset(Mutation):
    dataset: DatasetSpec


class CreateTask(Mutation):
    task: TaskSpec


class Assignment(Mutation):
    assignee: Identifier


class Draft(Mutation):
    annotation: Annotation
    correction: bool = Field(default=False, strict=True)


class Decision(Mutation):
    decision: Literal["confirmed", "rejected", "needs_clarification"]
    evidence_reference: Name


class PoolConfirmation(Mutation):
    query_id: Identifier
    reviewed_task_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=64)
    coverage_note: Name
    evidence_reference: Name


class EvaluationRequest(Mutation):
    export_id: Identifier
    results: RetrievalResults


class Acceptance(Mutation):
    report_id: Identifier
    decision: Literal[
        "accepted", "accepted_with_limitations", "rejected", "not_evaluable"
    ]
    limitations: tuple[Name, ...] = Field(max_length=16)


class TaskState(Versioned):
    task: TaskSpec
    status: Literal[
        "pending", "in_review", "confirmed", "rejected", "needs_clarification"
    ]
    annotation: Annotation | None
    review: IndependentReview | None
    assisted: bool = Field(strict=True)


class ReviewRevision(Versioned):
    entity: str = Field(min_length=1, max_length=200)
    previous: Sha | None
    previous_revision: Sha | None
    actor: Identifier
    time: datetime
    reason: str = Field(min_length=1, max_length=500)
    idempotency_key: Identifier
    intent: Sha
    binding: DatasetBinding
    value: dict[str, JsonValue]

    @model_validator(mode="after")
    def utc(self):
        if self.time.utcoffset() is None or self.time.utcoffset().total_seconds() != 0:
            raise ValueError("UTC audit timestamp required")
        return self


class EntityReply(Versioned):
    revision: Sha
    value: dict[str, JsonValue]
    current: bool | None = None
    blocked_by_security: bool | None = None
