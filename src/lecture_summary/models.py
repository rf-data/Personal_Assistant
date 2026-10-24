"""Portable summary-v1 contracts. Technical validity never proves subject accuracy."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from src.content_store.models import ContentLocator, Name, fingerprint
from src.job_control.models import Contract, Identifier, Sha

Text = Annotated[str, Field(min_length=1, max_length=6000)]
Quality = Literal[
    "verified_from_source", "uncertain", "requires_visual_context", "unsupported"
]
PROMPT_VERSION = "lecture-summary-de-v1"
TEMPLATE_VERSION = "lecture-print-de-v1"
SOURCE_ADAPTER_VERSION = "lecture-sources-v2"


class Artifact(Contract):
    """Identity is independent of location; version is the exact file SHA256."""

    artifact_id: Name
    storage_id: Identifier
    relative_path: str = Field(min_length=1, max_length=2000)
    sha256: Sha
    format: Literal["txt", "md", "transcript_json", "document_json", "knowledge_json"]
    role: Literal["original", "derived"] = "original"
    title: Name
    parent_artifact_ids: tuple[Name, ...] = ()
    source_url: str | None = Field(default=None, max_length=4096)


class Lecture(Contract):
    provider_id: Name
    course_id: Name
    lecture_id: Name
    title: Name
    sources: tuple[Artifact, ...] = Field(max_length=32)


class Catalog(Contract):
    schema_version: Literal[1] = 1
    lectures: tuple[Lecture, ...] = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def unique(self):
        keys = [(v.provider_id, v.course_id, v.lecture_id) for v in self.lectures]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate lecture identity / contradictory metadata")
        artifacts = {}
        for lecture in self.lectures:
            if len({s.artifact_id for s in lecture.sources}) != len(lecture.sources):
                raise ValueError("Duplicate source artifact in lecture")
            for source in lecture.sources:
                identity = (
                    lecture.provider_id,
                    lecture.course_id,
                    source.sha256,
                    source.format,
                )
                if (
                    source.artifact_id in artifacts
                    and artifacts[source.artifact_id] != identity
                ):
                    raise ValueError("Conflicting artifact identity/version")
                artifacts[source.artifact_id] = identity
        return self


class Options(Contract):
    detail: Literal["compact", "detailed"] = "compact"
    focus: str = Field(default="Grundlagen verstehen", max_length=300)


class Selection(Contract):
    provider_id: Name
    course_id: Name
    lecture_ids: tuple[Name, ...] = Field(min_length=1, max_length=3)
    options: Options = Options()

    @model_validator(mode="after")
    def unique(self):
        if len(set(self.lecture_ids)) != len(self.lecture_ids):
            raise ValueError("Select distinct lectures explicitly")
        return self


class Evidence(Contract):
    source_id: Name
    provider_id: Name
    course_id: Name
    lecture_id: Name
    artifact_id: Name
    artifact_sha256: Sha
    artifact_role: Literal["original", "derived"]
    document_id: Name
    chunk_id: Name
    title: Name
    source_url: str | None = None
    parent_artifact_ids: tuple[Name, ...] = ()
    native_source_id: Name | None = None
    native_document_id: Name | None = None
    native_chunk_id: Name | None = None
    native_item_id: Name | None = None
    parent_segment_ids: tuple[int, ...] = Field(default=(), max_length=1600)
    media_id: Name | None = None
    original_artifact_sha256: Sha | None = None
    text: Text
    locator: ContentLocator
    warnings: tuple[str, ...] = ()


class Claim(Contract):
    text: Text
    source_ids: tuple[Name, ...] = Field(max_length=32)
    kind: Literal["derived", "didactic_explanation", "external"] = "derived"
    quality: Quality = "uncertain"
    # Exact excerpt, checked against each cited evidence block.
    evidence_quote: str | None = Field(default=None, max_length=6000)


class Formula(Claim):
    latex: str = Field(min_length=1, max_length=1500)
    notation: Text
    assumptions: Text


class Topic(Contract):
    title: Name
    explanations: tuple[Claim, ...] = Field(min_length=1, max_length=30)
    definitions: tuple[Claim, ...] = Field(default=(), max_length=20)
    formulas: tuple[Formula, ...] = Field(default=(), max_length=20)
    examples: tuple[Claim, ...] = Field(default=(), max_length=20)
    misconceptions: tuple[Claim, ...] = Field(default=(), max_length=20)
    questions: tuple[Claim, ...] = Field(default=(), max_length=20)


class Draft(Contract):
    title: Name
    learning_objectives: tuple[Claim, ...] = Field(min_length=1, max_length=20)
    prerequisites: tuple[Claim, ...] = Field(default=(), max_length=20)
    topics: tuple[Topic, ...] = Field(min_length=1, max_length=12)
    takeaways: tuple[Claim, ...] = Field(min_length=1, max_length=20)
    processed_lecture_ids: tuple[Name, ...] = Field(min_length=1, max_length=3)
    missing_lecture_ids: tuple[Name, ...] = Field(default=(), max_length=3)


class Summary(Contract):
    schema_version: Literal[1] = 1
    summary_id: Sha
    selection: Selection
    artifact_versions: tuple[tuple[str, str], ...]
    model: Name
    prompt_version: str = PROMPT_VERSION
    template_version: str = TEMPLATE_VERSION
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content: Draft
    evidence: tuple[Evidence, ...]
    validation_status: Literal["passed", "needs_review", "failed"]
    validation_messages: tuple[str, ...]
    export_metadata: dict[str, str] = Field(
        default_factory=lambda: {
            "markdown": "utf-8; commonmark; lecture-summary-v1",
            "latex": TEMPLATE_VERSION + "; lualatex; no compilation performed",
            "source_adapter": SOURCE_ADAPTER_VERSION,
        }
    )


def cache_key(selection, versions, model):
    return fingerprint(
        {
            "schema": 1,
            "source_adapter": SOURCE_ADAPTER_VERSION,
            "selection": selection.model_dump(mode="json"),
            "versions": versions,
            "model": model,
            "prompt": PROMPT_VERSION,
            "template": TEMPLATE_VERSION,
        }
    )
