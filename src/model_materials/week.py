"""Additive week planning contracts; existing discovery, receipts and jobs stay v1."""

from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, field_validator, model_validator

from src.job_control.models import Contract, Sha
from src.model_materials.materials import MaterialResource, ParserConfig
from src.model_materials.media_plan import EvidenceRef
from src.workflows.models import relative


class WeekLimits(Contract):
    max_materials: int = Field(default=8, strict=True, ge=1, le=8)
    max_bytes: int = Field(default=1048576, strict=True, ge=1, le=1048576)
    total_raw_bytes: int = Field(default=8 * 1048576, strict=True, ge=1, le=8 * 1048576)
    reserve_bytes: int = Field(default=5 * 1024**3, strict=True, ge=5 * 1024**3)
    max_parallel: Literal[1] = 1
    max_queued: Literal[1] = 1
    wall_seconds: Literal[90] = 90
    cpu_seconds: Literal[60] = 60
    memory_mb: Literal[768] = 768
    parser_memory_mb: Literal[512] = 512
    max_blocks: Literal[1000] = 1000
    max_pdf_pages: Literal[20] = 20


class LocalSource(Contract):
    material_id: str
    path: Path
    expected_sha256: Sha | None = None

    @field_validator("path")
    @classmethod
    def absolute(cls, path):
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError("Explicit absolute source path required")
        return path


class DiscoverySnapshot(Contract):
    """Explicit existing export; no URL acquisition or implicit directory search."""

    label: str
    role: Literal["assignment", "lecture_notes"] = "assignment"
    path: Path
    original_url: HttpUrl
    sha256: Sha

    _label = field_validator("label")(relative)

    @field_validator("path")
    @classmethod
    def absolute(cls, path):
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError("Explicit absolute discovery export path required")
        return path


class WorkflowReference(Contract):
    material_id: str
    controller_root: Path
    job_id: str = Field(pattern=r"^job_[0-9a-f]{32}$")
    relative_path: str
    sha256: Sha

    _relative = field_validator("relative_path")(relative)

    @model_validator(mode="after")
    def binding(self):
        if not self.controller_root.is_absolute() or ".." in self.controller_root.parts:
            raise ValueError("Explicit controller root required")
        if not self.relative_path.startswith(f"jobs/{self.job_id}/results/"):
            raise ValueError(
                "Artifact must be relative to the declared controller root/job"
            )
        return self


class WeekRequest(Contract):
    schema_version: Literal[1] = 1
    manifest: Path
    course_id: Literal["cs50_python"] = "cs50_python"
    week: str = Field(default="0", pattern=r"^\d{1,2}$")
    mode: Literal[
        "discovery_only", "plan", "process_existing", "approved_acquisition"
    ] = "discovery_only"
    material_types: tuple[Literal["html", "pdf", "transcript", "media"], ...] = (
        "html",
        "pdf",
        "transcript",
        "media",
    )
    material_ids: tuple[str, ...] = ()
    source_origin: Literal["official", "synthetic"] = "official"
    discovery_exports: tuple[DiscoverySnapshot, ...] = Field(default=(), max_length=8)
    local_sources: tuple[LocalSource, ...] = Field(default=(), max_length=32)
    evidence: tuple[EvidenceRef, ...] = Field(default=(), max_length=32)
    workflow_references: tuple[WorkflowReference, ...] = Field(
        default=(), max_length=32
    )
    # Operator observations inform a plan; execution must recheck the actual host.
    available_bytes: int | None = Field(default=None, strict=True, ge=0)
    available_memory_mb: int | None = Field(default=None, strict=True, ge=0)
    existing_worker_confirmed: bool = Field(default=False, strict=True)
    limits: WeekLimits = Field(default_factory=WeekLimits)

    @model_validator(mode="after")
    def unique(self):
        if not self.manifest.is_absolute() or ".." in self.manifest.parts:
            raise ValueError("Explicit absolute manifest required")
        if len({s.label for s in self.discovery_exports}) != len(
            self.discovery_exports
        ) or len({str(s.original_url) for s in self.discovery_exports}) != len(
            self.discovery_exports
        ):
            raise ValueError("Duplicate discovery export")
        for entries in (self.local_sources, self.evidence, self.workflow_references):
            if len({e.material_id for e in entries}) != len(entries):
                raise ValueError("Duplicate per-material evidence")
        if (
            len(set(self.material_types)) != len(self.material_types)
            or not self.material_types
        ):
            raise ValueError("Explicit unique material types required")
        if len(set(self.material_ids)) != len(self.material_ids):
            raise ValueError("Duplicate material scope")
        if self.mode == "discovery_only" and (
            self.local_sources or self.evidence or self.workflow_references
        ):
            raise ValueError("Discovery-only does not inspect material artifacts")
        return self


class Snapshot(Contract):
    source_kind: Literal["versioned_fixture", "operator_supplied_export"] = (
        "versioned_fixture"
    )
    file: str
    original_url: str
    sha256: Sha


class WeekResource(Contract):
    binding: MaterialResource
    resource_id: str
    material_id: str
    title: str
    parent_resource_ids: tuple[str, ...] = ()
    variant_aliases: tuple[str, ...] = ()
    category: Literal[
        "html", "pdf", "transcript", "media", "code", "presentation", "unknown"
    ]
    acquisition_policy: Literal["approval_required", "manual_only", "review_required"]
    adapter: Literal[
        "c18_material",
        "offline_transcript",
        "media_plan_only",
        "presentation_export",
        "manual_code",
        "unsupported",
    ]
    discovery_status: Literal[
        "not_examined", "discovered", "classified", "ambiguous"
    ] = "classified"
    acquisition_status: Literal[
        "not_requested",
        "approval_required",
        "approved",
        "local_present",
        "verified",
        "blocked",
        "manual_required",
    ] = "not_requested"
    processing_status: Literal[
        "not_requested",
        "queued",
        "running",
        "completed",
        "failed",
        "unsupported",
        "blocked",
    ] = "not_requested"
    quality_status: Literal[
        "not_checked", "passed", "passed_with_warnings", "verified_transcript", "failed"
    ] = "not_checked"
    parser: ParserConfig | None = None
    processor: str | None = None
    planned_steps: tuple[str, ...] = ()
    local_snapshots: tuple[Snapshot, ...] = ()
    selected: bool = False
    action: Literal[
        "none",
        "reference_only",
        "blocked",
        "reuse_verified_result",
        "ready_c18_submission",
        "ready_transcript_import",
        "acquisition_plan_only",
    ] = "none"
    missing_approvals: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    raw_sha256: Sha | None = None
    raw_bytes: int | None = None
    workflow_references: tuple[WorkflowReference, ...] = Field(
        default=(), max_length=32
    )
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def identities(self):
        if (self.resource_id, self.material_id) != (
            self.binding.source_id,
            self.binding.material_id,
        ):
            raise ValueError("Week identity differs from existing material binding")
        if self.acquisition_policy == "manual_only" and self.action not in {
            "none",
            "reference_only",
            "blocked",
        }:
            raise ValueError(
                "Manual resources cannot enter automatic processing/acquisition"
            )
        return self


def week_counts(resources, gaps):
    return dict(
        resources=len({r.resource_id for r in resources}),
        material_variants=len(resources),
        supported=sum(
            r.adapter in {"c18_material", "offline_transcript"} for r in resources
        ),
        locally_present=sum(
            (bool(r.local_snapshots) and r.category in {"html", "pdf", "transcript"})
            or r.acquisition_status in {"local_present", "verified"}
            for r in resources
        ),
        verified=sum(r.acquisition_status == "verified" for r in resources),
        processed=sum(r.processing_status == "completed" for r in resources),
        blocked=sum(
            bool(r.blockers or r.missing_approvals) or r.acquisition_status == "blocked"
            for r in resources
        ),
        manual_only=sum(r.acquisition_policy == "manual_only" for r in resources),
        open_issues=sum(
            bool(r.blockers or r.missing_approvals) or r.quality_status == "failed"
            for r in resources
        ),
        selected=sum(r.selected for r in resources),
        ready=sum(
            r.action in {"ready_c18_submission", "ready_transcript_import"}
            for r in resources
        ),
        reused=sum(r.action == "reuse_verified_result" for r in resources),
        gaps=len(gaps),
    )


class WeekReport(Contract):
    schema_version: Literal[1] = 1
    planner_version: Literal["c26_week_materials_v1"] = "c26_week_materials_v1"
    course_id: Literal["cs50_python"]
    week: str
    mode: str
    request_sha256: Sha
    manifest_sha256: Sha
    snapshots: tuple[Snapshot, ...]
    resources: tuple[WeekResource, ...] = Field(max_length=128)
    scope_material_ids: tuple[str, ...]
    counts: dict[str, int]
    gaps: tuple[str, ...]
    limits: WeekLimits
    snapshot_inventory_complete: Literal[True] = True
    full_week_discovery_verified: Literal[False] = False
    scope_processing_complete: bool
    technical_workflow_complete: bool
    subject_matter_verified: Literal[False] = False
    production_observation: Literal["not_checked"] = "not_checked"
    execution_supported: Literal[False] = False

    @model_validator(mode="after")
    def consistency(self):
        mids = [r.material_id for r in self.resources]
        ids = {r.resource_id for r in self.resources}
        selected = [r for r in self.resources if r.selected]
        complete = bool(selected) and all(
            r.processing_status == "completed"
            and not r.blockers
            and not r.missing_approvals
            for r in selected
        )
        if (
            len(set(mids)) != len(mids)
            or tuple(r.material_id for r in selected) != self.scope_material_ids
            or self.counts != week_counts(self.resources, self.gaps)
            or self.scope_processing_complete != complete
            or self.technical_workflow_complete != complete
        ):
            raise ValueError(
                "Week report counts, scope or completion contradict resource observations"
            )
        if any(
            r.binding.resource.course_id != self.course_id
            or self.week not in r.binding.resource.section_keys
            or set(r.parent_resource_ids) - ids
            for r in self.resources
        ):
            raise ValueError("Week report graph/course/parent mismatch")
        return self
