"""Small execution envelopes around existing C16 and material contracts."""

from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from src.job_control.models import Contract, Course, Identifier, ScopeId, Sha

Relative = Annotated[str, Field(min_length=1, max_length=400)]
StageStatus = Literal[
    "pending",
    "ready",
    "running",
    "completed",
    "skipped",
    "blocked",
    "stale",
    "failed",
    "cancelled",
    "interrupted",
]
VALID = {"completed", "skipped"}


def relative(value):
    p = PurePosixPath(value)
    if (
        p.is_absolute()
        or ".." in p.parts
        or "\\" in value
        or p.as_posix() != value
        or value == "."
    ):
        raise ValueError("Portable relative artifact path required")
    return value


class Definition(Contract):
    schema_version: Literal[1] = 1
    workflow_type: Literal["cs50_offline_materials_v1"] = "cs50_offline_materials_v1"
    course_id: Course
    section: ScopeId | None = None
    lecture_ids: tuple[ScopeId, ...] = ()
    sources: dict[ScopeId, Relative] = Field(min_length=1, max_length=3)
    source_origin: Literal["official", "synthetic"] = "official"
    max_bytes: int = Field(default=524288, ge=1, le=1048576)
    max_blocks: int = Field(default=1000, ge=1, le=2000)
    continue_independent: bool = Field(default=True, strict=True)

    @model_validator(mode="after")
    def paths(self):
        for path in self.sources.values():
            relative(path)
        if len(set(self.sources.values())) != len(self.sources) or len(
            set(self.lecture_ids)
        ) != len(self.lecture_ids):
            raise ValueError("Duplicate sources or lecture IDs")
        return self


class Output(Contract):
    kind: Literal["plan", "raw", "receipt", "normalized", "image", "quality", "handoff"]
    identity: str = Field(min_length=1, max_length=200)
    path: Relative
    sha256: Sha
    size_bytes: int = Field(ge=0, le=8388608)

    _relative = field_validator("path")(relative)


class Stage(Contract):
    stage_id: ScopeId
    process_id: Identifier
    material_id: str | None = None
    dependencies: tuple[ScopeId, ...] = ()
    expected_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    missing_inputs: tuple[str, ...] = ()
    contract_version: Literal[1] = 1
    configuration_hash: Sha
    status: StageStatus = "pending"
    decision: str = "not_examined"
    input_hashes: dict[str, Sha] = Field(default_factory=dict)
    output_refs: tuple[Output, ...] = ()
    stale_reasons: tuple[str, ...] = ()
    error: str | None = Field(default=None, max_length=200)
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    job_id: Identifier | None = None


class Workflow(Contract):
    schema_version: Literal[1] = 1
    workflow_id: Identifier
    workflow_type: Literal["cs50_offline_materials_v1"] = "cs50_offline_materials_v1"
    course_id: Course
    lecture_ids: tuple[ScopeId, ...]
    created_at: str | None
    status: StageStatus
    stages: tuple[Stage, ...] = Field(max_length=13)
    dependencies: dict[str, tuple[str, ...]]
    input_refs: tuple[Identifier, ...]
    output_refs: tuple[Output, ...] = ()
    configuration_hash: Sha
    run_id: Identifier | None = None
    initiated_by: Identifier
    started_at: str | None = None
    finished_at: str | None = None
    expected_changes: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    report_sha256: Sha

    @model_validator(mode="after")
    def graph_contract(self):
        from src.workflows.graph import topological

        if topological(self.stages) != self.stages or self.dependencies != {
            s.stage_id: s.dependencies for s in self.stages
        }:
            raise ValueError("Workflow graph/order contradicts stage definitions")
        return self


class State(Contract):
    schema_version: Literal[1] = 1
    report: Workflow
    attempts: tuple[Identifier, ...] = Field(max_length=10)

    @model_validator(mode="after")
    def current_attempt(self):
        if (
            not self.attempts
            or len(set(self.attempts)) != len(self.attempts)
            or self.report.run_id != self.attempts[-1]
        ):
            raise ValueError("Persisted workflow must identify its current C16 attempt")
        return self
