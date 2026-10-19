"""Versioned transport/configuration contracts; no Knowledge business models."""

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.model_discovery.cs50 import CourseId as Course

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")]
ScopeId = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_:.-]{0,159}$")]
Sha = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Status = Literal[
    "created",
    "queued",
    "running",
    "cancel_requested",
    "completed",
    "failed",
    "cancelled",
    "interrupted",
]
TERMINAL = {"completed", "failed", "cancelled", "interrupted"}


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Principal(Contract):
    subject: Identifier
    role: Literal["viewer", "operator"]
    courses: tuple[Course, ...]


class Identity(Principal):
    token_sha256: Sha


class CatalogEntry(Contract):
    kind: Literal[
        "manifest", "material_bundle", "workflow_bundle", "pdf_bundle", "index_bundle"
    ]
    root: Path
    files: dict[str, Sha] = Field(min_length=1, max_length=128)
    roles: dict[str, str]
    course_ids: tuple[Course, ...]

    @model_validator(mode="after")
    def paths(self):
        for value in self.files:
            path = PurePosixPath(value)
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in value
                or path.as_posix() != value
            ):
                raise ValueError("Catalog paths must be portable relative names")
        expected = (
            {"manifest"}
            if self.kind == "manifest"
            else {"manifest", "workflow"}
            if self.kind == "workflow_bundle"
            else {"receipt", "raw"}
            if self.kind == "pdf_bundle"
            else {"index"}
            if self.kind == "index_bundle"
            else {"plan", "normalized", "receipt", "raw"}
        )
        if set(self.roles) != expected or not set(self.roles.values()) <= set(
            self.files
        ):
            raise ValueError("Catalog roles must resolve exclusively to declared files")
        if not self.root.is_absolute() or not self.course_ids:
            raise ValueError("Absolute approved root and course scope required")
        return self


class Settings(Contract):
    schema_version: Literal[1] = 1
    root: Path
    catalog: dict[Identifier, CatalogEntry] = Field(default_factory=dict, max_length=32)
    identities: tuple[Identity, ...] = ()
    execution_enabled: bool = Field(default=False, strict=True)
    workflows_enabled: bool = Field(default=False, strict=True)
    pdf_enabled: bool = Field(default=False, strict=True)
    index_jobs_enabled: bool = Field(default=False, strict=True)
    max_jobs: int = Field(default=100, ge=1, le=1000)
    max_queued: int = Field(default=8, ge=1, le=32)
    max_parallel: int = Field(default=1, ge=1, le=2)
    worker_ttl: float = Field(default=5, ge=1, le=30)

    @model_validator(mode="after")
    def private_paths(self):
        repo = Path(__file__).resolve().parents[2]
        root = self.root
        if (
            not root.is_absolute()
            or root == Path("/")
            or ".." in root.parts
            or root.is_relative_to(repo)
            or repo.is_relative_to(root)
        ):
            raise ValueError(
                "Job workspace must be an explicit external private directory"
            )
        subjects = [i.subject for i in self.identities]
        tokens = [i.token_sha256 for i in self.identities]
        if len(set(subjects)) != len(subjects) or len(set(tokens)) != len(tokens):
            raise ValueError("Identity subjects and token digests must be unique")
        for entry in self.catalog.values():
            if (
                entry.root == root
                or entry.root.is_relative_to(root)
                or root.is_relative_to(entry.root)
            ):
                raise ValueError(
                    "Approved inputs and private job workspace must be separate"
                )
        return self


class PlanningParams(Contract):
    source_ref: Identifier
    course_id: Course
    section: ScopeId | None = None
    resource_id: ScopeId | None = None
    output_name: Identifier = "material-plan"


class QualityParams(Contract):
    material_ref: Identifier
    course_id: Course
    output_name: Identifier = "quality-report"


class WorkflowParams(Contract):
    source_ref: Identifier
    course_id: Course
    workflow_id: Identifier
    previous_run_id: Identifier | None = None
    output_name: Identifier = "workflow-report"


class PdfParams(Contract):
    material_ref: Identifier
    course_id: Course
    output_name: Identifier = "pdf-receipt"


class IndexParams(Contract):
    schema_version: Literal[1] = 1
    source_ref: Identifier
    course_id: Course
    resume_of: Identifier | None = None
    output_name: Identifier = "index-build"


class PreviewRequest(Contract):
    schema_version: Literal[1] = 1
    process_id: Identifier
    parameters: dict


class Preview(Contract):
    schema_version: Literal[1] = 1
    preview_id: Sha
    process_id: Identifier
    parameters: dict
    input_refs: tuple[Identifier, ...]
    expected_artifacts: tuple[str, ...]


class StartRequest(Contract):
    schema_version: Literal[1] = 1
    preview: Preview
    confirmed: Literal[True]
    start: bool = Field(default=True, strict=True)

    @field_validator("confirmed", mode="before")
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True:
            raise ValueError("Explicit boolean confirmation required")
        return value


class Artifact(Contract):
    schema_version: Literal[1] = 1
    artifact_id: Identifier
    job_id: Identifier
    kind: Literal[
        "material_plan",
        "quality_report",
        "workflow_report",
        "material_receipt",
        "index_build",
    ]
    size_bytes: int = Field(ge=0)
    sha256: Sha
    created_at: str
    input_refs: tuple[Identifier, ...]


class Job(Contract):
    schema_version: Literal[1] = 1
    job_id: Identifier
    process_id: Identifier
    status: Status
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    parameters: dict
    progress: None = None
    phase: str
    exit_code: int | None = None
    error: str | None = Field(default=None, max_length=200)
    error_class: Literal["input", "timeout", "internal", "other"] | None = None
    artifact_refs: tuple[Artifact, ...] = Field(default=(), max_length=1)
    initiated_by: Identifier
    input_refs: tuple[Identifier, ...] = Field(min_length=1, max_length=1)
    output_refs: tuple[Identifier, ...] = Field(default=(), max_length=1)
    cancellable: bool = False
    duration_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def consistent_job(self):
        from src.job_control.registry import process_for

        params = (
            process_for(self.process_id)
            .model.model_validate(self.parameters)
            .model_dump(mode="json")
        )
        ref = params.get("source_ref", params.get("material_ref"))
        if params != self.parameters or self.input_refs != (ref,):
            raise ValueError("Stored parameters/input identity contradict registry")
        if (self.status in TERMINAL) != (self.finished_at is not None):
            raise ValueError("Terminal state requires a confirmed end timestamp")
        if self.cancellable != (self.status in {"queued", "running"}):
            raise ValueError("Cancellation capability contradicts status")
        if self.output_refs != tuple(a.artifact_id for a in self.artifact_refs) or any(
            a.job_id != self.job_id for a in self.artifact_refs
        ):
            raise ValueError("Artifact references contradict job identity")
        if self.status == "completed" and (
            self.exit_code != 0 or not self.artifact_refs
        ):
            raise ValueError("Completion needs a successful exit and published output")
        return self


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load_settings(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 1024 * 1024:
        raise ValueError("Configuration must be a bounded regular file")
    return Settings.model_validate_json(path.read_bytes())
