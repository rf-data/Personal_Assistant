"""Versioned planning inputs; no execution capabilities or new workflow engine."""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from src.job_control.models import Contract, Sha
from src.model_discovery.cs50 import CourseId, NonEmpty
from src.model_discovery.cs50_selection import SelectionPolicy

State = Literal[
    "available_local",
    "available_remote",
    "verified",
    "approved",
    "unsupported",
    "missing",
    "blocked",
    "not_required",
    "requires_visual_context",
    "ready_for_processing",
]


class MediaLimits(Contract):
    """Separate conservative media proposal limits, never document byte limits."""

    audio_bytes: int = Field(default=64 * 1024**2, strict=True, ge=1, le=64 * 1024**2)
    video_bytes: int = Field(default=128 * 1024**2, strict=True, ge=1, le=128 * 1024**2)
    scratch_bytes: int = Field(
        default=512 * 1024**2, strict=True, ge=1, le=512 * 1024**2
    )
    reserve_bytes: int = Field(default=5 * 1024**3, strict=True, ge=5 * 1024**3)
    duration_seconds: float = Field(default=600, gt=0, le=600, allow_inf_nan=False)
    wall_seconds: int = Field(default=120, strict=True, ge=1, le=120)
    cpu_seconds: int = Field(default=60, strict=True, ge=1, le=60)
    memory_mb: int = Field(default=1024, strict=True, ge=256, le=1024)
    cpu_threads: Literal[1] = 1
    concurrent_jobs: Literal[1] = 1
    max_frames: int = Field(default=12, strict=True, ge=1, le=12)


class TimeWindow(Contract):
    start: float = Field(ge=0, allow_inf_nan=False)
    end: float = Field(gt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def bounded(self):
        if not 0 < self.end - self.start <= 60:
            raise ValueError("Visual window must be ordered and at most 60 seconds")
        return self


class EvidenceRef(Contract):
    material_id: NonEmpty
    kind: Literal["transcript", "material", "media"]
    workspace: Path
    receipt_sha256: Sha | None = None
    batch: Path | None = None
    plan: Path | None = None
    relative_path: str | None = None

    @model_validator(mode="after")
    def paths_and_contract(self):
        for path in (self.workspace, self.batch, self.plan):
            if path is not None and (not path.is_absolute() or ".." in path.parts):
                raise ValueError("Explicit absolute evidence paths required")
        if self.kind == "media":
            path = Path(self.relative_path or "")
            if (
                not self.relative_path
                or path.is_absolute()
                or ".." in path.parts
                or "\\" in self.relative_path
                or path.as_posix() != self.relative_path
            ):
                raise ValueError("Normalized relative media path required")
        elif (
            self.receipt_sha256 is None
            or (self.kind == "transcript" and self.batch is None)
            or (self.kind == "material" and self.plan is None)
        ):
            raise ValueError("Existing pinned receipt and batch/plan required")
        return self


class Adequacy(Contract):
    """Purpose-specific operator assessment, never independent human gold."""

    material_id: NonEmpty
    raw_sha256: Sha
    purpose: NonEmpty
    text: Literal["adequate", "inadequate", "unknown"] = "unknown"
    visual: Literal["adequate", "inadequate", "unknown"] = "unknown"
    decision_reference: NonEmpty


class Unavailability(Contract):
    material_id: NonEmpty
    reason: Literal[
        "missing", "inadequate", "not_applicable", "access_denied", "technical_failure"
    ]
    decision_reference: NonEmpty


class MediaEstimate(Contract):
    material_id: NonEmpty
    bytes: int = Field(strict=True, gt=0, le=2 * 1024**3)
    duration_seconds: float = Field(gt=0, allow_inf_nan=False)
    estimate_reference: NonEmpty


class MediaRequest(Contract):
    schema_version: Literal[1] = 1
    manifest: Path
    course_id: CourseId
    lecture_id: NonEmpty
    subject_id: NonEmpty | None = None  # Optional independent Short subject.
    purpose: NonEmpty
    need_text: bool = Field(default=True, strict=True)
    need_visual: bool = Field(default=False, strict=True)
    source_origin: Literal["official", "synthetic"] = "official"
    policy: SelectionPolicy = Field(
        default_factory=lambda: SelectionPolicy(preferred_video_resolution="360p")
    )
    evidence: tuple[EvidenceRef, ...] = Field(default=(), max_length=32)
    adequacy: tuple[Adequacy, ...] = Field(default=(), max_length=32)
    unavailable: tuple[Unavailability, ...] = Field(default=(), max_length=64)
    estimates: tuple[MediaEstimate, ...] = Field(default=(), max_length=32)
    visual_windows: tuple[TimeWindow, ...] = Field(default=(), max_length=4)
    resource_probe_root: Path
    limits: MediaLimits = Field(default_factory=MediaLimits)

    @model_validator(mode="after")
    def unique(self):
        for entries in (self.evidence, self.adequacy, self.unavailable, self.estimates):
            if len({e.material_id for e in entries}) != len(entries):
                raise ValueError("Duplicate per-material planning input")
        if not self.need_text and not self.need_visual:
            raise ValueError("Explicit text or visual purpose required")
        if sum(w.end - w.start for w in self.visual_windows) > 120:
            raise ValueError("Combined visual window bound exceeded")
        if self.visual_windows and not self.need_visual:
            raise ValueError("Visual windows need an explicit visual purpose")
        for path in (self.manifest, self.resource_probe_root):
            if not path.is_absolute() or ".." in path.parts:
                raise ValueError("Explicit absolute planning roots required")
        return self
