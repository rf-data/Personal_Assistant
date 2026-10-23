"""Bounded course planning and read-only preflight using the existing B5 planner.

No execution token is produced. Live admission remains with C16 and the separately
reviewed deployment gate; operator capacity observations are planning inputs only.
"""

from pathlib import Path
from urllib.parse import urlsplit

from src.job_control.catalog import read_file
from src.job_control.models import fingerprint
from src.model_materials.course import (
    CourseReport,
    CourseRequest,
    PreflightCheck,
    PreflightReport,
    WeekOutcome,
    course_counts,
)
from src.model_materials.week import ProfiledWeekRequest
from src.tools_lecture import material_handoff
from src.tools_materials import batch as api
from src.tools_materials import mapping, parse_html, parse_pdf, quality, transcripts
from src.tools_materials.week import plan_week, routing

LIVE_BLOCKERS = {
    "capacity_unknown_or_insufficient_including_5gib_reserve",
    "memory_capacity_unknown_or_insufficient",
    "existing_single_worker_and_queue_limits_not_confirmed",
}


def contracts_revision():
    from src.job_control import registry
    from src.model_materials import assignments as assignment_models
    from src.model_materials import course as course_models
    from src.model_materials import materials
    from src.model_materials import week as week_models
    from src.tools_materials import assignments, capacity, processing, profiles, week
    from src.workflows import definition
    from src.workflows import models as workflow_models

    return fingerprint(
        {
            module.__name__: api.sha(read_file(Path(module.__file__)))
            for module in (
                materials,
                parse_html,
                parse_pdf,
                quality,
                mapping,
                material_handoff,
                transcripts,
                definition,
                api,
                capacity,
                profiles,
                week,
                week_models,
                course_models,
                registry,
                assignments,
                assignment_models,
                processing,
                workflow_models,
            )
        }
    )


def profile_format(profile):
    data = profile.model_dump(
        mode="json",
        exclude={
            "course_id",
            "manifest_sha256",
            "snapshots",
            "sections",
            "adapter_sha256",
        },
    )
    data["required_role_sets"] = sorted(
        {
            tuple(sorted(role.value for role in section.required_roles))
            for section in profile.sections
        }
    )
    return fingerprint(data)


def pilot_decision(request):
    ref = request.reference
    if not ref:
        return 3, ("review_offline_reference_and_adapter",)
    categories, actions = [1], []
    if request.infrastructure_revision != ref.infrastructure_revision:
        categories.append(5)
        actions.append("infrastructure_comparison_and_separate_acceptance_required")
    if contracts_revision() != ref.contracts_sha256:
        categories.append(4)
        actions.append("parser_schema_handoff_regression_and_targeted_pilot")
    if (
        request.profile.adapter_sha256 != ref.adapter_sha256
        or profile_format(request.profile) != ref.profile_format_sha256
        or set(request.material_types) - set(ref.material_types)
    ):
        categories.append(3)
        actions.append("targeted_adapter_or_material_offline_pilot")
    if request.course_id != ref.course_id:
        categories.append(2)
        actions.append("new_course_adapter_sample_acceptance")
    return max(categories), tuple(actions) or ("regular_batch_preflight",)


def policy_grant(request, binding, week, existing=None):
    """Prepare only the exact resources and flags explicitly reviewed by operator."""
    matches = [
        (p, s)
        for p in request.policies
        for s in p.sources
        if s.material_id == binding.material_id
    ]
    if len(matches) != 1:
        raise PermissionError("unique_explicit_source_policy_review_required")
    policy, review = matches[0]
    now = request.evaluated_at
    if now is None:
        raise PermissionError("approval_evaluation_time_unknown")
    if policy.revoked:
        raise PermissionError("approval_revoked")
    if not policy.valid_from <= now < policy.expires_at:
        raise PermissionError("approval_expired_or_not_yet_valid")
    if (
        not policy.status_checked_at
        <= now
        <= policy.status_checked_at + policy.status_max_age_seconds
    ):
        raise PermissionError("approval_revocation_status_stale_or_future")
    url = urlsplit(binding.original_url)
    if (
        policy.course_id != binding.resource.course_id
        or review.source_id != binding.source_id
        or review.original_url != binding.original_url
        or week not in review.sections
        or week not in binding.resource.section_keys
        or review.role.value != binding.role
        or review.format != binding.format
        or review.conditions_sha256 != policy.conditions_sha256
        or url.scheme != "https"
        or url.username
        or url.password
        or f"{url.scheme}://{url.netloc}" not in policy.origins
    ):
        raise PermissionError("approval_scope_origin_role_or_conditions_changed")
    grant = api.SourceApproval(
        material_id=binding.material_id,
        source_id=binding.source_id,
        course_id=policy.course_id,
        original_url=binding.original_url,
        approval_reference=policy.approval_reference,
        usage_reference=policy.purpose,
        license_review_reference=policy.license_review_reference,
        robots_review_reference=policy.robots_review_reference,
        retention_reference=policy.retention_reference,
        revocation_reference=policy.revocation_reference,
        expected_sha256=review.expected_sha256,
        download=review.download,
        process=review.process,
    )
    if review.grant_sha256 is not None:
        if (
            existing is None
            or fingerprint(existing.model_dump(mode="json")) != review.grant_sha256
        ):
            raise PermissionError("explicit_reviewed_grant_missing_or_changed")
        for field in (
            "material_id",
            "source_id",
            "course_id",
            "original_url",
            "expected_sha256",
            "download",
            "process",
        ):
            if getattr(existing, field) != getattr(grant, field):
                raise PermissionError(
                    "existing_grant_contradicts_explicit_source_review"
                )
        grant = existing
    use = dict(
        policy_id=policy.policy_id,
        policy_sha256=fingerprint(policy.model_dump(mode="json")),
        material_id=binding.material_id,
        source_id=binding.source_id,
        grant_sha256=fingerprint(grant.model_dump(mode="json")),
        evaluated_at=str(now),
        week=week,
        process=str(grant.process).lower(),
        download=str(grant.download).lower(),
    )
    return grant, use


def week_request(request, key):
    return next(
        (w for w in request.week_inputs if w.week == key), None
    ) or ProfiledWeekRequest(
        manifest=request.manifest,
        profile=request.profile,
        course_id=request.course_id,
        week=key,
        mode=request.mode,
        material_types=request.material_types,
        selection=request.selection,
        source_origin=request.source_origin,
    )


def _inventory_request(week):
    return ProfiledWeekRequest.model_validate(
        week.model_dump()
        | dict(
            mode="discovery_only", local_sources=(), evidence=(), workflow_references=()
        )
    )


def _groups(outcomes):
    groups = {}
    for w in outcomes:
        if w.report:
            for row in w.report.resources:
                groups.setdefault(row.material_id, []).append((w.week, row))
    shared = {
        mid: tuple(key for key, _ in rows)
        for mid, rows in groups.items()
        if len(rows) > 1
    }
    conflicts = []
    for mid, rows in groups.items():
        identities = {
            fingerprint(row.binding.model_dump(mode="json")) for _, row in rows
        }
        digests = {r.raw_sha256 for _, r in rows if r.raw_sha256}
        if len(identities) != 1 or len(digests) > 1:
            conflicts.append(mid)
    return groups, shared, tuple(sorted(conflicts))


def _preflight(request, outcomes, plan_sha, conflicts, policy_checks, pilot):
    checks = []

    def check(code, scope, status, reason, required=True, digest=None):
        checks.append(
            PreflightCheck(
                code=code,
                scope=scope,
                status=status,
                reason=reason,
                required=required,
                evidence_sha256=digest,
            )
        )

    check(
        "identity_conflicts",
        request.course_id,
        "fail" if conflicts else "pass",
        ",".join(conflicts) or "Stable material bindings and raw digests",
    )
    q = request.queue_observation
    fresh = (
        q is not None
        and request.evaluated_at is not None
        and q.observed_at <= request.evaluated_at <= q.observed_at + 300
    )
    queue_status = (
        "unknown"
        if not fresh
        else (
            "pass"
            if q.queued_jobs < 1 and q.running_jobs <= 1 and q.worker_instances == 1
            else "fail"
        )
    )
    check(
        "planning_queue",
        request.course_id,
        queue_status,
        "Operator observation only; one worker, at most one occupied queue slot; freshness <=300s",
        required=q is not None or request.environment == "production",
        digest=fingerprint(q.model_dump(mode="json")) if q else None,
    )
    check(
        "pilot_reference",
        request.course_id,
        "pass" if pilot == 1 else "fail",
        "Reference contract match"
        if pilot == 1
        else "Additional targeted acceptance required",
    )
    handoff = material_handoff.LectureMaterialHandoff.model_fields[
        "schema_version"
    ].default
    check(
        "handoff_version",
        request.course_id,
        "pass" if handoff >= request.minimum_handoff_version else "fail",
        f"Available handoff v{handoff}; requested minimum v{request.minimum_handoff_version}",
    )
    automatic, manual = [], []
    for outcome in outcomes:
        key = outcome.week
        if outcome.error:
            check("week_discovery", key, "fail", outcome.error)
            continue
        report = outcome.report
        wr = week_request(request, key)
        from src.job_control.registry import WORKFLOW_PROCESS

        check(
            "guardian_budgets",
            key,
            "pass"
            if (
                wr.limits.wall_seconds <= WORKFLOW_PROCESS.timeout_seconds
                and wr.limits.cpu_seconds <= WORKFLOW_PROCESS.cpu_seconds
                and wr.limits.memory_mb * 1048576 <= WORKFLOW_PROCESS.memory_bytes
            )
            else "fail",
            "Planning budgets must fit the existing C16 registry",
        )
        check(
            "week_discovery",
            key,
            "pass",
            "Pinned manifest/profile and existing B5 identities",
            digest=report.request_sha256,
        )
        missing = [
            g
            for g in report.gaps
            if g.startswith(("required_role_missing:", "task_not_proven:"))
        ]
        check(
            "required_resources",
            key,
            "fail" if missing else "pass",
            ",".join(missing) or "Expected roles/references present",
        )
        check(
            "planning_capacity",
            key,
            "unknown"
            if wr.available_bytes is None or wr.available_memory_mb is None
            else "pass"
            if wr.available_bytes
            >= wr.limits.reserve_bytes + wr.limits.total_raw_bytes * 4 + 528 * 1048576
            and wr.available_memory_mb >= wr.limits.memory_mb
            else "fail",
            "Operator planning observation; does not prove live worker readiness",
            required=wr.available_bytes is not None
            or wr.available_memory_mb is not None,
        )
        check(
            "bounded_batch_scope",
            key,
            "pass" if report.counts["selected"] <= wr.limits.max_materials else "fail",
            "Existing maximum material count retained; scope never truncated",
        )
        for row in report.resources:
            if not row.selected:
                continue
            scope = key + ":" + row.material_id
            if row.acquisition_policy == "manual_only":
                manual.append(row)
                check(
                    "manual_code_policy",
                    scope,
                    "pass",
                    "Reference only; explicit import workflow required",
                )
                continue
            automatic.append(row)
            error = policy_checks.get((key, row.material_id))
            check(
                "source_approval_policy",
                scope,
                "fail" if error else "pass",
                error or "Exact reviewed grant; validity and revocation checked",
            )
            blockers = (
                tuple(b for b in row.blockers if b not in LIVE_BLOCKERS)
                + row.missing_approvals
            )
            if row.binding.role not in {
                r.value for r in request.profile.material_roles
            }:
                blockers += ("role_outside_profile",)
            if row.category not in request.profile.processing_routes:
                blockers += ("processing_route_outside_profile",)
            if not row.binding.resource.provenance:
                blockers += ("missing_discovery_provenance",)
            if routing(row.binding, wr.limits)[1] == "manual_only":
                blockers += ("manual_policy_changed_during_planning",)
            check(
                "material_binding_raw_parser_quality",
                scope,
                "fail" if blockers else "pass",
                ",".join(blockers)
                or "Existing B5 raw/receipt/parser/quality checks passed",
                digest=row.raw_sha256,
            )
    check(
        "nonempty_processing_scope",
        request.course_id,
        "pass" if automatic or manual else "fail",
        "Explicit selected resources"
        if automatic or manual
        else "No processing scope selected",
    )
    live = request.environment == "production"
    for code, reason in (
        (
            "live_worker_queue",
            "Fresh worker/heartbeat/queue admission evidence is unavailable",
        ),
        (
            "persistent_paths_capacity",
            "Live persistent mounts, writable roots and remaining capacity unverified",
        ),
        (
            "deployment_gate",
            "Issue #146: productive gate/driver acceptance not demonstrated",
        ),
    ):
        check(code, request.course_id, "unknown", reason, required=live)
    if any(c.required and c.status in {"unknown", "fail"} for c in checks):
        decision = "blocked"
    elif manual and not automatic:
        decision = "operator_action_required"
    elif manual or any(c.status in {"unknown", "fail"} for c in checks):
        decision = "ready_with_warnings"
    else:
        decision = "ready"
    return PreflightReport(
        environment=request.environment,
        plan_sha256=plan_sha,
        checks=tuple(checks),
        decision=decision,
    )


def plan_course(request, approvals=None):
    request = CourseRequest.model_validate_json(request.model_dump_json())
    approvals = api.Approvals.model_validate_json(
        (approvals or api.Approvals()).model_dump_json()
    )
    outcomes, used, policy_errors = [], [], {}
    for key in request.weeks:
        try:
            week = week_request(request, key)
            inventory = plan_week(_inventory_request(week))
            grants = {g.material_id: g for g in approvals.sources}
            for row in inventory.resources:
                if row.acquisition_policy == "manual_only":
                    continue
                try:
                    prepared, use = policy_grant(
                        request, row.binding, key, grants.get(row.material_id)
                    )
                    if (
                        row.material_id in grants
                        and grants[row.material_id] != prepared
                    ):
                        raise PermissionError(
                            "concrete_grant_differs_from_reviewed_policy"
                        )
                    grants[row.material_id] = prepared
                    used.append(use)
                except PermissionError as exc:
                    grants.pop(row.material_id, None)
                    policy_errors[(key, row.material_id)] = str(exc)
            known = {r.material_id for r in inventory.resources}
            scoped = api.Approvals(
                sources=tuple(g for mid, g in grants.items() if mid in known),
                min_interval_seconds=approvals.min_interval_seconds,
            )
            report = plan_week(week, scoped)
            outcomes.append(WeekOutcome(week=key, report=report))
        except (OSError, ValueError, RuntimeError) as exc:
            outcomes.append(WeekOutcome(week=key, error=str(exc)))
    groups, shared, conflicts = _groups(outcomes)
    selected = {
        (w.week, r.material_id)
        for w in outcomes
        if w.report
        for r in w.report.resources
        if r.selected and r.acquisition_policy != "manual_only"
    }
    used = tuple(u for u in used if (u["week"], u["material_id"]) in selected)
    pilot, actions = pilot_decision(request)
    contracts = contracts_revision()
    inputs = dict(
        request_sha256=fingerprint(request.model_dump(mode="json")),
        approvals_sha256=fingerprint(approvals.model_dump(mode="json")),
        contracts_sha256=contracts,
        weeks=tuple(outcomes),
        profile=request.profile,
        shared_materials=shared,
        identity_conflicts=conflicts,
        approvals_used=used,
        pilot_category=pilot,
        pilot_actions=actions,
    )
    # canonical() handles only JSON values; persist the exact nested reports.
    plan_sha = fingerprint(
        {
            k: [w.model_dump(mode="json") for w in v]
            if k == "weeks"
            else v.model_dump(mode="json")
            if k == "profile"
            else v
            for k, v in inputs.items()
        }
    )
    preflight = _preflight(request, outcomes, plan_sha, conflicts, policy_errors, pilot)
    selected_rows = [r for _, rows in groups.items() for _, r in rows if r.selected]
    complete = (
        bool(selected_rows)
        and not conflicts
        and not any(w.error for w in outcomes)
        and all(
            r.processing_status == "completed"
            and not r.blockers
            and not r.missing_approvals
            for r in selected_rows
        )
    )
    return CourseReport(
        course_id=request.course_id,
        **inputs,
        plan_sha256=plan_sha,
        counts=course_counts(outcomes, used),
        preflight=preflight,
        technical_processing_complete=complete,
    )


def preflight_course(request, approvals=None):
    """Recompute observations; never accept a previous report as an admission grant."""
    return plan_course(request, approvals).preflight


def plan_courses(requests, approvals=None):
    requests = tuple(requests)
    if not 1 <= len(requests) <= 6 or len({r.course_id for r in requests}) != len(
        requests
    ):
        raise ValueError("Select one to six distinct supported courses")
    return tuple(plan_course(r, approvals) for r in requests)
