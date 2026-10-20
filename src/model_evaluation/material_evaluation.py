"""Evaluation-only corpus/review contracts; reuse Content locators and B bundles."""

from datetime import date
from pathlib import PurePosixPath
from typing import Literal

from pydantic import Field, JsonValue, model_validator

from src.content_store.inventory import InventorySelection
from src.content_store.models import ContentLocator, canonical, sha256
from src.job_control.models import Contract, Identifier, Sha
from src.model_course import ContentCourseId as CourseId

Origin = Literal["real", "synthetic", "unknown"]
Format = Literal["html", "pdf", "code", "srt", "txt"]
Dimension = Literal[
    "text", "structure", "code", "formula", "image", "table", "transcript", "locator"
]


class CorpusEntry(Contract):
    entry_id: Identifier
    origin: Origin
    course_id: CourseId
    source_id: str | None = Field(default=None, min_length=1, max_length=500)
    material_id: str | None = None
    section_keys: tuple[str, ...] = ()
    lecture_ids: tuple[str, ...] = ()
    format: Format
    original_url: str | None = None
    root_key: Identifier
    # Explicit local artifacts, never discovery roots or URL downloads.
    artifacts: dict[Literal["raw", "parsed", "receipt", "quality"], str] = Field(
        default_factory=dict
    )
    raw_sha256: Sha | None = None
    permission: Literal["inventory_only", "evaluation", "denied"]
    permission_reference: str = Field(min_length=1, max_length=2000)
    notes: tuple[str, ...] = ()
    selection: InventorySelection | None = None

    @model_validator(mode="after")
    def explicit_paths(self):
        for value in self.artifacts.values():
            path = PurePosixPath(value)
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in value
                or path.as_posix() != value
            ):
                raise ValueError("Corpus artifacts require normalized relative paths")
        if self.selection is not None:
            if (self.source_id, self.course_id) != (
                self.selection.source_id,
                self.selection.course_id,
            ):
                raise ValueError(
                    "Corpus identity contradicts existing bundle selection"
                )
            if self.artifacts:
                raise ValueError("Bundle paths come only from InventorySelection")
            if (self.format == "srt") != (self.selection.kind == "srt"):
                raise ValueError("Corpus format contradicts bundle kind")
        return self


class CorpusManifest(Contract):
    schema_version: Literal[1]
    dataset_version: str = Field(min_length=1, max_length=100)
    entries: tuple[CorpusEntry, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def unique(self):
        if len({e.entry_id for e in self.entries}) != len(self.entries):
            raise ValueError("Duplicate corpus entry_id")
        return self


class GoldReference(Contract):
    gold_id: Identifier
    entry_id: Identifier
    source_id: str | None = Field(default=None, min_length=1, max_length=500)
    source_version_id: str | None = None
    original_sha256: Sha
    dimension: Dimension
    source_reference: str = Field(min_length=1, max_length=2000)
    created_date: date
    target_pointer: str | None = Field(default=None, pattern=r"^/", max_length=2000)
    expected_content: str | None = Field(default=None, max_length=100000)
    expected_structure: dict[str, JsonValue] | None = Field(default=None, min_length=1)
    expected_locator: ContentLocator | None = None
    expected_occurrences: int | None = Field(default=None, ge=0, strict=True)
    reference_status: Literal["confirmed", "pending_review", "rejected"]
    method: Literal[
        "independent_source_annotation", "parser_preannotation", "synthetic_reference"
    ]
    reviewer: str | None = Field(default=None, min_length=1, max_length=200)
    review_reference: str | None = Field(default=None, min_length=1, max_length=2000)
    review_date: date | None = None
    notes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def independent_review(self):
        if self.expected_occurrences is not None and self.expected_content is None:
            raise ValueError("Occurrence reference needs independent expected content")
        if (
            self.expected_locator is not None
            and self.expected_locator.raw_artifact_sha256 != self.original_sha256
        ):
            raise ValueError("Gold locator raw hash conflict")
        if self.reference_status == "confirmed":
            if not all(
                (
                    self.source_id,
                    self.target_pointer,
                    self.source_version_id,
                    self.reviewer,
                    self.review_reference,
                    self.review_date,
                )
            ):
                raise ValueError(
                    "Confirmed gold needs source version and independent review evidence"
                )
            if self.method == "parser_preannotation":
                raise ValueError(
                    "Parser preannotation is pending, never independent gold"
                )
            if (
                self.expected_content is None
                and self.expected_structure is None
                and self.expected_locator is None
            ):
                raise ValueError(
                    "Confirmed gold needs an explicit expected observation"
                )
        return self


class GoldDataset(Contract):
    schema_version: Literal[1]
    dataset_version: str = Field(min_length=1, max_length=100)
    references: tuple[GoldReference, ...] = Field(max_length=2000)

    @model_validator(mode="after")
    def unique(self):
        if len({r.gold_id for r in self.references}) != len(self.references):
            raise ValueError("Duplicate gold_id")
        return self


class EvaluationReport(Contract):
    report: dict[str, JsonValue]
    sha256: Sha

    @model_validator(mode="after")
    def digest(self):
        if (
            self.report.get("schema_version") != 1
            or self.report.get("evaluator_version") != "cs50_corpus_evaluation_v1"
        ):
            raise ValueError("Unknown corpus report version")
        if sha256(canonical(self.report)) != self.sha256:
            raise ValueError("Corpus report digest mismatch")
        return self
