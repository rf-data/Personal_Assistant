"""Bounded envelopes around B5; no new execution, queue or receipt contracts."""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from src.job_control.models import Contract, Sha, fingerprint
from src.model_discovery.cs50 import CourseId, ResourceRole
from src.model_materials.week import (
    CourseProfile,
    ProfiledWeekReport,
    ProfiledWeekRequest,
)


class SourceReview(Contract):
    material_id: str
    source_id: str
    original_url: str
    sections: tuple[str, ...] = Field(min_length=1, max_length=32)
    role: ResourceRole
    format: str
    conditions_sha256: Sha
    expected_sha256: Sha | None = None
    grant_sha256: Sha | None = None
    download: bool = Field(default=False, strict=True)
    process: bool = Field(default=False, strict=True)


class ApprovalPolicy(Contract):
    """Shared evidence plus explicit reviews; never a grant for future resources."""

    schema_version: Literal[1] = 1
    policy_id: str = Field(min_length=1, max_length=100)
    course_id: CourseId
    purpose: str = Field(min_length=1, max_length=1000)
    origins: tuple[str, ...] = Field(min_length=1, max_length=8)
    conditions_sha256: Sha
    valid_from: int = Field(strict=True, ge=1)
    expires_at: int = Field(strict=True, ge=1)
    status_checked_at: int = Field(strict=True, ge=1)
    status_max_age_seconds: int = Field(default=300, strict=True, ge=1, le=3600)
    revoked: bool = Field(strict=True)
    approval_reference: str = Field(min_length=1)
    license_review_reference: str = Field(min_length=1)
    robots_review_reference: str = Field(min_length=1)
    retention_reference: str = Field(min_length=1)
    revocation_reference: str = Field(min_length=1)
    sources: tuple[SourceReview, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def bounded_grants(self):
        if self.expires_at <= self.valid_from or len(
            {s.material_id for s in self.sources}
        ) != len(self.sources):
            raise ValueError("Invalid validity interval or duplicate source review")
        if any(
            not getattr(self, k).strip()
            for k in type(self).model_fields
            if k.endswith("_reference")
        ):
            raise ValueError("Nonblank policy evidence required")
        return self


class ReferenceAcceptance(Contract):
    schema_version: Literal[1] = 1
    reference: str = Field(min_length=1)
    course_id: CourseId
    profile_format_sha256: Sha
    adapter_sha256: Sha
    contracts_sha256: Sha
    material_types: tuple[str, ...] = Field(min_length=1, max_length=4)
    infrastructure_revision: str = Field(min_length=1)


class QueueObservation(Contract):
    """Operator planning evidence, never an authenticated live admission check."""

    queued_jobs: int = Field(strict=True, ge=0, le=1000)
    running_jobs: int = Field(strict=True, ge=0, le=1000)
    worker_instances: int = Field(strict=True, ge=0, le=32)
    observed_at: int = Field(strict=True, ge=1)
    reference: str = Field(min_length=1, max_length=2000)


class CourseRequest(Contract):
    schema_version: Literal[1] = 1
    manifest: Path
    course_id: CourseId
    profile: CourseProfile
    weeks: tuple[str, ...] = Field(min_length=1, max_length=8)
    mode: Literal[
        "discovery_only", "plan", "process_existing", "approved_acquisition"
    ] = "plan"
    material_types: tuple[Literal["html", "pdf", "transcript", "media"], ...] = (
        "html",
        "pdf",
        "transcript",
    )
    selection: Literal["types", "all", "complete"] = "types"
    source_origin: Literal["official", "synthetic"] = "official"
    week_inputs: tuple[ProfiledWeekRequest, ...] = Field(default=(), max_length=8)
    policies: tuple[ApprovalPolicy, ...] = Field(default=(), max_length=8)
    evaluated_at: int | None = Field(default=None, strict=True, ge=1)
    reference: ReferenceAcceptance | None = None
    infrastructure_revision: str | None = None
    environment: Literal["offline", "production"] = "offline"
    minimum_handoff_version: Literal[1, 2] = 1
    queue_observation: QueueObservation | None = None

    @model_validator(mode="after")
    def scope(self):
        if not self.manifest.is_absolute() or ".." in self.manifest.parts:
            raise ValueError("Explicit absolute manifest required")
        if self.course_id != self.profile.course_id or len(set(self.weeks)) != len(
            self.weeks
        ):
            raise ValueError("Course mismatch or duplicate week")
        if not set(self.weeks) <= {s.key for s in self.profile.sections}:
            raise ValueError("Week outside registered profile")
        if not self.material_types or len(set(self.material_types)) != len(
            self.material_types
        ):
            raise ValueError("Explicit unique material types required")
        if len({w.week for w in self.week_inputs}) != len(self.week_inputs):
            raise ValueError("Duplicate week input")
        for w in self.week_inputs:
            if (
                w.week not in self.weeks
                or w.course_id != self.course_id
                or w.manifest != self.manifest
                or w.profile != self.profile
                or w.source_origin != self.source_origin
            ):
                raise ValueError("Week input contradicts course/profile/snapshot scope")
        if len({p.policy_id for p in self.policies}) != len(self.policies):
            raise ValueError("Duplicate approval policy")
        return self


class PreflightCheck(Contract):
    code: str
    scope: str
    required: bool
    status: Literal["pass", "fail", "unknown", "not_applicable"]
    reason: str
    evidence_sha256: Sha | None = None


class PreflightReport(Contract):
    schema_version: Literal[1] = 1
    environment: Literal["offline", "production"]
    plan_sha256: Sha
    checks: tuple[PreflightCheck, ...]
    decision: Literal[
        "ready", "ready_with_warnings", "operator_action_required", "blocked"
    ]
    production_decision: Literal["blocked"] = "blocked"
    execution_supported: Literal[False] = False

    @model_validator(mode="after")
    def fail_closed(self):
        blocked = any(
            c.required and c.status in {"fail", "unknown"} for c in self.checks
        )
        if blocked != (self.decision == "blocked"):
            raise ValueError("Preflight decision contradicts mandatory checks")
        if self.environment == "production" and self.decision != "blocked":
            raise ValueError("Production adapter and live gate are not integrated")
        return self


class WeekOutcome(Contract):
    week: str
    report: ProfiledWeekReport | None = None
    error: str | None = None

    @model_validator(mode="after")
    def result(self):
        if (self.report is None) == (self.error is None) or (
            self.report and self.report.week != self.week
        ):
            raise ValueError("Exactly one matching week report or error required")
        return self


def course_counts(weeks, used=()):
    groups = {}
    for week in weeks:
        if week.report:
            for row in week.report.resources:
                groups.setdefault(row.material_id, []).append(row)
    return dict(
        resources=len({r.resource_id for rows in groups.values() for r in rows}),
        material_variants=len(groups),
        selected=sum(any(r.selected for r in rows) for rows in groups.values()),
        locally_present=sum(
            any(
                r.raw_sha256
                or (r.local_snapshots and r.category in {"html", "pdf", "transcript"})
                for r in rows
            )
            for rows in groups.values()
        ),
        approved_sources=len(
            {u["material_id"] for u in used if u["process"] == "true"}
        ),
        supported=sum(
            any(r.adapter in {"c18_material", "offline_transcript"} for r in rows)
            for rows in groups.values()
        ),
        processed=sum(
            any(r.processing_status == "completed" for r in rows)
            for rows in groups.values()
        ),
        reused=sum(
            any(r.action == "reuse_verified_result" for r in rows)
            for rows in groups.values()
        ),
        blocked=sum(
            any(r.blockers or r.missing_approvals for r in rows)
            for rows in groups.values()
        ),
        blocked_in_scope=sum(
            any(r.selected and (r.blockers or r.missing_approvals) for r in rows)
            for rows in groups.values()
        ),
        unselected=sum(not any(r.selected for r in rows) for rows in groups.values()),
        excluded=sum(
            any(r.acquisition_policy == "manual_only" for r in rows)
            for rows in groups.values()
        ),
        failed_weeks=sum(w.error is not None for w in weeks),
    )


class CourseReport(Contract):
    schema_version: Literal[1] = 1
    course_id: CourseId
    profile: CourseProfile
    request_sha256: Sha
    approvals_sha256: Sha
    contracts_sha256: Sha
    plan_sha256: Sha
    weeks: tuple[WeekOutcome, ...] = Field(min_length=1, max_length=8)
    counts: dict[str, int]
    shared_materials: dict[str, tuple[str, ...]]
    identity_conflicts: tuple[str, ...]
    approvals_used: tuple[dict[str, str], ...]
    pilot_category: Literal[1, 2, 3, 4, 5]
    pilot_actions: tuple[str, ...]
    preflight: PreflightReport
    discovery_complete: Literal[False] = False
    technical_processing_complete: bool
    subject_matter_complete: Literal[False] = False
    execution_supported: Literal[False] = False

    @model_validator(mode="after")
    def consistency(self):
        fields = (
            "request_sha256",
            "approvals_sha256",
            "contracts_sha256",
            "weeks",
            "profile",
            "shared_materials",
            "identity_conflicts",
            "approvals_used",
            "pilot_category",
            "pilot_actions",
        )
        data = self.model_dump(mode="json")
        if self.plan_sha256 != fingerprint({k: data[k] for k in fields}):
            raise ValueError("Course plan digest mismatch")
        if (
            len({w.week for w in self.weeks}) != len(self.weeks)
            or self.profile.course_id != self.course_id
        ):
            raise ValueError("Duplicate weeks or foreign profile")
        selected = [
            r for w in self.weeks if w.report for r in w.report.resources if r.selected
        ]
        complete = (
            bool(selected)
            and not self.identity_conflicts
            and not any(w.error for w in self.weeks)
            and all(
                r.processing_status == "completed"
                and not r.blockers
                and not r.missing_approvals
                for r in selected
            )
        )
        shared = {}
        for w in self.weeks:
            if w.report:
                if w.report.course_id != self.course_id:
                    raise ValueError("Foreign week report")
                if w.report.profile_sha256 != fingerprint(
                    self.profile.model_dump(mode="json")
                ):
                    raise ValueError("Foreign week profile")
                for r in w.report.resources:
                    shared.setdefault(r.material_id, []).append(w.week)
        shared = {mid: tuple(keys) for mid, keys in shared.items() if len(keys) > 1}
        if (
            self.counts != course_counts(self.weeks, self.approvals_used)
            or self.shared_materials != shared
            or self.technical_processing_complete != complete
            or self.preflight.plan_sha256 != self.plan_sha256
        ):
            raise ValueError("Course report counts, scope or completion mismatch")
        return self
