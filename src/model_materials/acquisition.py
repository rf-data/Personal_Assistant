"""Download-only week contracts, additive to the existing material bindings."""

from typing import Literal

from pydantic import Field, model_validator

from src.job_control.models import Contract, Sha
from src.model_discovery.cs50 import CourseId

MIB = 1024**2
Status = Literal[
    "DISCOVERED",
    "APPROVAL_PENDING",
    "DOWNLOADED",
    "VERIFIED",
    "REFERENCED_ONLY",
    "FALLBACK_SELECTED",
    "MANUAL_PENDING",
    "MANUAL_VERIFIED",
    "MISSING",
    "BLOCKED",
    "FAILED",
    "NOT_APPLICABLE",
]


class AcquisitionLimits(Contract):
    html_bytes: int = Field(default=MIB, strict=True, gt=0, le=MIB)
    text_bytes: int = Field(default=MIB, strict=True, gt=0, le=MIB)
    subtitle_bytes: int = Field(default=2 * MIB, strict=True, gt=0, le=2 * MIB)
    pdf_bytes: int = Field(default=8 * MIB, strict=True, gt=0, le=8 * MIB)
    manual_bytes: int = Field(default=8 * MIB, strict=True, gt=0, le=8 * MIB)
    transfer_bytes: int = Field(default=32 * MIB, strict=True, gt=0, le=32 * MIB)
    archive_bytes: int = Field(default=64 * MIB, strict=True, ge=MIB, le=64 * MIB)
    report_bytes: int = Field(default=16 * MIB, strict=True, ge=MIB, le=16 * MIB)
    reserve_bytes: int = Field(default=5 * 1024**3, strict=True, ge=5 * 1024**3)
    max_parallel: Literal[1] = 1
    max_materials: int = Field(default=256, strict=True, gt=0, le=256)
    wall_seconds: int = Field(default=540, strict=True, gt=0, le=540)

    def ceiling(self, material):
        if material.material_type == "source_code":
            return self.manual_bytes
        if material.source_format == "pdf":
            return self.pdf_bytes
        if material.material_type == "subtitles":
            return self.subtitle_bytes
        if material.source_format == "html":
            return self.html_bytes
        return self.text_bytes


class WeekMaterial(Contract):
    course_id: CourseId
    week_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,40}$")
    section_id: str
    material_id: str
    parent_material_id: str | None = None
    material_type: Literal[
        "course",
        "week",
        "lecture",
        "shorts",
        "short",
        "problem_set",
        "task",
        "page",
        "transcript",
        "subtitles",
        "audio",
        "video",
        "slides",
        "notes",
        "source_code",
        "attachment",
        "reference",
    ]
    title: str
    source_url: str | None = None
    discovered_from: tuple[str, ...] = ()
    source_format: str = "html"
    expected_local_path: str | None = None
    required: bool = False
    acquisition_strategy: str = "reference"
    acquisition_priority: int = 0
    acquisition_status: Status = "DISCOVERED"
    review_status: Literal["PENDING", "APPROVED", "NOT_REQUIRED"] = "PENDING"
    manual_action_required: bool = False
    file_size: int | None = Field(default=None, strict=True, ge=0)
    sha256: Sha | None = None
    receipt_id: str | None = None
    error_reason: str | None = None
    alternative_group: str | None = None
    selected: bool = False
    discovery_examined: bool = False
    description: str | None = None
    metadata: dict = Field(default_factory=dict)


class WeekInventory(Contract):
    schema_version: Literal[1] = 1
    kind: Literal["c26-week-acquisition"] = "c26-week-acquisition"
    course_id: CourseId = "cs50_python"
    week_id: str = Field(default="0", pattern=r"^[A-Za-z0-9_-]{1,40}$")
    source_origin: Literal["official", "synthetic"] = "official"
    materials: tuple[WeekMaterial, ...] = Field(min_length=1, max_length=256)
    # Separate expectation ledger detects deleted rows, including individual tasks.
    expected_ids: tuple[str, ...] = Field(min_length=1, max_length=256)
    expected_parents: dict[str, str | None] = Field(default_factory=dict)
    expected_types: dict[str, str] = Field(default_factory=dict)
    snapshots: tuple[dict, ...] = ()
    limits: AcquisitionLimits = Field(default_factory=AcquisitionLimits)
    processing_enabled: Literal[False] = False
    c26_status: Literal["HOLD"] = "HOLD"

    @model_validator(mode="after")
    def graph(self):
        rows = {m.material_id: m for m in self.materials}
        courses = [r for r in self.materials if r.material_type == "course"]
        weeks = [r for r in self.materials if r.material_type == "week"]
        if (
            len(courses) != 1
            or len(weeks) != 1
            or courses[0].parent_material_id is not None
            or weeks[0].parent_material_id != courses[0].material_id
            or not any(r.material_type == "lecture" for r in self.materials)
        ):
            raise ValueError("Explicit course/week/lecture scope required")
        if len(rows) != len(self.materials) or len(self.expected_ids) != len(
            set(self.expected_ids)
        ):
            raise ValueError("Duplicate week identity")
        for row in self.materials:
            if (row.course_id, row.week_id) != (self.course_id, self.week_id):
                raise ValueError("Week/course mismatch")
            visited, parent = {row.material_id}, row.parent_material_id
            while parent is not None:
                if parent not in rows or parent in visited:
                    raise ValueError("Unknown/cyclic material parent")
                visited.add(parent)
                parent = rows[parent].parent_material_id
        return self


class SourceGrant(Contract):
    material_id: str
    source_url: str
    source_format: str
    max_bytes: int = Field(strict=True, gt=0, le=8 * MIB)
    license_reviewed: Literal[True]
    purpose: Literal["download", "discovery"] = "download"


class WeekApproval(Contract):
    schema_version: Literal[1] = 1
    inventory_sha256: Sha
    source_origin: Literal["official", "synthetic"]
    reviewed_by: str = Field(min_length=1, max_length=120)
    review_reference: str = Field(min_length=1, max_length=300)
    transfer_bytes: int = Field(strict=True, gt=0, le=32 * MIB)
    grants: tuple[SourceGrant, ...] = Field(max_length=256)

    @model_validator(mode="after")
    def unique(self):
        if len({g.material_id for g in self.grants}) != len(self.grants):
            raise ValueError("Duplicate source grant")
        return self
