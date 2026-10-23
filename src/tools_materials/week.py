"""Read-only week inventory and admission plans around existing C26 adapters.

No downloader, worker, queue, transcriber or provider is started here. A ready
batch is an input for the existing reviewed C16/C18 path, never an execution grant.
"""

from pathlib import Path
from types import SimpleNamespace
from urllib.parse import unquote, urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import fingerprint
from src.job_control.pdf_adapter import PDF_CONFIG
from src.model_discovery.cs50 import Provenance, ResourceCandidate
from src.model_materials.materials import MaterialResource, ParserConfig
from src.model_materials.media_plan import MediaLimits
from src.model_materials.week import (
    ProfiledWeekReport,
    ProfiledWeekRequest,
    Snapshot,
    WeekReport,
    WeekRequest,
    WeekResource,
    week_counts,
)
from src.tools_lecture.cs50_manifest import load_fixture_manifest
from src.tools_materials import batch as api
from src.tools_materials import media_evidence, transcripts
from src.tools_materials.inventory import CODE, official
from src.tools_materials.parse_html import dom_path
from src.tools_materials.processing import make_plan
from src.tools_materials.profiles import EXPECTED_TASKS, validate_profile


def routing(binding, limits):
    """Policy precedes parser selection, including misleading roles/format hints."""
    path = unquote(unquote(urlsplit(binding.original_url).path)).lower()
    suffix = Path(path).suffix.lstrip(".")
    fmt = binding.format.lower()
    code_path = any(
        p in {"src", "code", "source_code", "sources"}
        or (p.startswith("src") and p[3:].isdigit())
        for p in path.split("/")
    )
    transcript = suffix == fmt and (binding.role, fmt) in {
        ("subtitles", "srt"),
        ("transcript", "txt"),
    }
    if (
        (suffix in (CODE | {"zip", "tar", "gz", "bz2", "xz", "7z"}) and not transcript)
        or (code_path and suffix != "pdf")
        or (binding.role == "source_code" and suffix != "pdf")
        or fmt in {"py", "zip"}
    ):
        return "code", "manual_only", "manual_code", None
    if binding.role in {"lecture_video", "audio", "short", "section", "demo"}:
        return "media", "approval_required", "media_plan_only", None
    if fmt in {"srt", "txt", "vtt"} and binding.role in {"transcript", "subtitles"}:
        return (
            "transcript",
            "approval_required",
            "offline_transcript" if transcripts.supported(binding) else "unsupported",
            None,
        )
    if urlsplit(binding.original_url).hostname == "docs.google.com":
        return "presentation", "review_required", "presentation_export", None
    if not official(binding.original_url):
        return "unknown", "review_required", "unsupported", None
    if suffix == "pdf" and fmt == "pdf":
        config = PDF_CONFIG.model_copy(
            update={"max_bytes": limits.max_bytes, "max_blocks": limits.max_blocks}
        )
        return "pdf", "approval_required", "c18_material", config
    if (
        fmt == "html"
        and (path.endswith("/") or suffix in {"html", "htm"})
        and binding.role in {"notes", "problem_set", "reference", "practice"}
    ):
        return (
            "html",
            "approval_required",
            "c18_material",
            ParserConfig(
                name="html",
                version="2",
                max_bytes=limits.max_bytes,
                max_blocks=limits.max_blocks,
                memory_mb=512,
                timeout=10,
            ),
        )
    return "unknown", "review_required", "unsupported", None


def _inventory(request):
    path = safe_path(request.manifest)
    manifest = load_fixture_manifest(path)
    profiled = isinstance(request, ProfiledWeekRequest)
    profile = validate_profile(request.profile, path) if profiled else None
    section = (
        next(s for s in profile.sections if s.key == request.week) if profile else None
    )
    graph = make_plan(path)  # Existing index/week parsing; never parse code indexes.
    course = next(
        (c for c in manifest.courses if c.course_id == request.course_id), None
    )
    if course is None:
        raise ValueError("Course is absent from supplied manifest")
    selected = [
        b.model_copy(update={"source_origin": request.source_origin})
        for b in graph.materials
        if b.resource.course_id == request.course_id
        and request.week in b.resource.section_keys
    ]
    if not selected:
        raise ValueError("Week is not present in supplied snapshots")
    native = {b.material_id for b in selected}
    parent_ids = {}
    # Only already supplied assignment snapshots are inspected. Never open URLs,
    # recursively follow links or read the supplied source_code_index DOM.
    parents = [
        b
        for b in selected
        if b.role == "problem_set"
        and (
            b.original_url in {str(u) for u in section.assignment_roots}
            if section
            else urlsplit(b.original_url).path == f"/python/psets/{request.week}/"
        )
    ]
    observed_pages = [
        p
        for p in course.pages
        if p.role == "course_index"
        or (
            p.role == "week_overview"
            and (
                str(p.url) == str(section.overview_url)
                if section
                else urlsplit(str(p.url)).path == f"/python/weeks/{request.week}/"
            )
        )
    ]
    extra_paths = {}
    additional_pages = []
    for supplied in request.discovery_exports:
        if supplied.label in {p.file for p in course.pages}:
            raise ValueError("Discovery export label collides with fixture")
        allowed = (
            any(str(supplied.original_url).startswith(b.original_url) for b in parents)
            if supplied.role == "assignment"
            else any(
                b.role == "notes" and b.original_url == str(supplied.original_url)
                for b in selected
            )
        )
        if not allowed:
            raise ValueError("Discovery export is outside a proven week resource")
        content = read_file(safe_path(supplied.path), request.limits.max_bytes)
        if api.sha(content) != supplied.sha256:
            raise ValueError("Discovery export hash mismatch")
        extra_paths[supplied.label] = supplied.path
        additional_pages.append(
            SimpleNamespace(
                file=supplied.label, url=supplied.original_url, role=supplied.role
            )
        )

    observed_pages.extend(p for p in additional_pages if p.role == "lecture_notes")

    def snapshot_path(page):
        return (
            safe_path(extra_paths[page.file])
            if page.file in extra_paths
            else safe_path(path.parent, page.file)
        )

    for parent in parents:
        base_path = urlsplit(parent.original_url).path
        for page in (*course.pages, *additional_pages):
            url = str(page.url)
            if page.role != "assignment" or not url.startswith(parent.original_url):
                continue
            raw = read_file(snapshot_path(page), 1048576)
            soup = BeautifulSoup(raw, "html.parser")
            main = soup.find("main")
            if main is None:
                continue
            observed_pages.append(page)
            candidates = []
            # The manifest URL itself proves the existence of a supplied child page.
            if url != parent.original_url:
                candidates.append((url, main.find("h1") or main))
            candidates.extend(
                (urldefrag(urljoin(url, str(a["href"])))[0], a)
                for a in main.select("a[href]")
            )
            for child_url, node in candidates:
                parsed = urlsplit(child_url)
                tail = parsed.path.removeprefix(base_path).strip("/")
                if (
                    (parsed.scheme, parsed.netloc) != ("https", "cs50.harvard.edu")
                    or parsed.query
                    or not parsed.path.startswith(base_path)
                    or not tail
                    or "/" in tail
                    or not parsed.path.endswith("/")
                ):
                    continue
                if node.find_parent(["nav", "aside", "footer"]) is not None:
                    continue
                evidence = Provenance(
                    original_url=url,
                    fixture_file=page.file,
                    locator=dom_path(node),
                    context_path=(
                        f"Week {request.week}",
                        "Problem Set",
                        node.get_text(" ", strip=True),
                    ),
                )
                matches = [
                    b
                    for b in selected
                    if b.original_url == child_url
                    and b.role == "problem_set"
                    and b.variant_id is None
                ]
                if matches:
                    binding = matches[0]
                    resource = binding.resource.model_copy(
                        update={
                            "provenance": tuple(
                                dict.fromkeys((*binding.resource.provenance, evidence))
                            )
                        }
                    )
                    # Provenance models contain no mutable data; de-duplicate by value below.
                    selected[selected.index(binding)] = binding.model_copy(
                        update={"resource": resource}
                    )
                else:
                    resource = ResourceCandidate(
                        course_id=request.course_id,
                        role="problem_set",
                        original_url=child_url,
                        title=node.get_text(" ", strip=True) or child_url,
                        section_keys=(request.week,),
                        parent_resource_id=parent.source_id,
                        format="html",
                        provenance=(evidence,),
                    )
                    binding = MaterialResource(
                        resource=resource,
                        lecture_ids=parent.lecture_ids,
                        original_url=child_url,
                        format="html",
                        role="problem_set",
                        source_origin=request.source_origin,
                    )
                    selected.append(binding)
                parent_ids.setdefault(binding.material_id, set()).add(parent.source_id)
    expanded, aliases = [], {}
    for binding in selected:
        expanded.append(binding)
        for variant in binding.resource.variants:
            if (
                str(variant.original_url) == binding.original_url
                and variant.language == binding.language
                and (variant.format or "unknown") == binding.format
            ):
                aliases.setdefault(binding.material_id, []).append(variant.variant_id)
                continue
            expanded.append(
                MaterialResource(
                    resource=binding.resource,
                    lecture_ids=binding.lecture_ids,
                    variant_id=variant.variant_id,
                    original_url=str(variant.original_url),
                    format=variant.format or "unknown",
                    role=binding.role,
                    language=variant.language,
                    source_origin=request.source_origin,
                )
            )
    snapshots = tuple(
        Snapshot(
            source_kind="operator_supplied_export"
            if p.file in extra_paths
            else "versioned_fixture",
            file=p.file,
            original_url=str(p.url),
            sha256=api.sha(read_file(snapshot_path(p))),
        )
        for p in {p.file: p for p in observed_pages}.values()
    )
    rows = []
    for binding in expanded:
        category, policy, adapter, parser = routing(binding, request.limits)
        limits = []
        processor = {
            "c18_material": "src.workflows.service.submit",
            "offline_transcript": "src.tools_materials.transcripts.run",
            "media_plan_only": "src.tools_materials.media_plan.plan",
        }.get(adapter)
        if binding.material_id not in native and adapter == "c18_material":
            limits.append("assignment_child_not_in_existing_c18_discovery_graph")
        if adapter == "media_plan_only":
            limits.append(
                "use_existing_media_plan_with_purpose_adequacy_and_capacity; no_week_media_execution"
            )
        rows.append(
            WeekResource(
                binding=binding,
                resource_id=binding.source_id,
                material_id=binding.material_id,
                title=binding.resource.title or binding.original_url,
                parent_resource_ids=tuple(
                    sorted(parent_ids.get(binding.material_id, set()))
                )
                or (
                    (binding.resource.parent_resource_id,)
                    if binding.resource.parent_resource_id
                    else ()
                ),
                variant_aliases=tuple(aliases.get(binding.material_id, ())),
                category=category,
                acquisition_policy=policy,
                adapter=adapter,
                parser=parser,
                processor=processor,
                acquisition_status="local_present"
                if category in {"html", "pdf", "transcript"}
                and any(s.original_url == binding.original_url for s in snapshots)
                else "not_requested",
                discovery_status="ambiguous" if category == "unknown" else "classified",
                local_snapshots=tuple(
                    s for s in snapshots if s.original_url == binding.original_url
                ),
                limitations=tuple(limits),
            )
        )
    return rows, snapshots, native


def resolve_workflow_reference(ref, maximum=1048576):
    """Do not add another jobs/ prefix: controller_root may itself be named jobs."""
    path = safe_path(ref.controller_root, ref.relative_path)
    raw = read_file(path, maximum)
    if api.sha(raw) != ref.sha256:
        raise ValueError("Workflow artifact hash changed")
    return path


def _observations(row, request, approvals):
    state = row.model_dump()
    binding = row.binding
    local = next(
        (i for i in request.local_sources if i.material_id == row.material_id), None
    )
    ref = next((e for e in request.evidence if e.material_id == row.material_id), None)
    workflow = next(
        (e for e in request.workflow_references if e.material_id == row.material_id),
        None,
    )
    blockers, missing = [], []
    if row.acquisition_policy == "manual_only":
        return row.model_copy(
            update={"acquisition_status": "manual_required", "action": "reference_only"}
        )
    if row.adapter in {"unsupported", "presentation_export"}:
        return row.model_copy(
            update={
                "processing_status": "unsupported",
                "acquisition_status": "blocked",
                "action": "blocked" if row.selected else "none",
                "blockers": ("unsupported_or_separate_export_review_required",),
            }
        )
    if row.local_snapshots and row.category in {"html", "pdf", "transcript"}:
        state["acquisition_status"] = "local_present"
    grant = None
    try:
        grant = api.approval(binding, approvals, "process")
    except PermissionError:
        if row.selected:
            missing.append("source_process_approval")
    if grant:
        state["acquisition_status"] = "approved"
    if local:
        try:
            raw = read_file(safe_path(local.path), request.limits.max_bytes)
            if not raw:
                raise ValueError("Empty local source")
            digest = api.sha(raw)
            state.update(
                acquisition_status="local_present",
                raw_bytes=len(raw),
                raw_sha256=digest,
            )
            if local.expected_sha256 is not None:
                if digest != local.expected_sha256:
                    raise ValueError("Local source hash changed")
                state["acquisition_status"] = "verified"
            if (
                not grant
                or grant.expected_sha256 != digest
                or local.expected_sha256 != digest
            ):
                blockers.append("local_source_not_pinned_to_current_source_approval")
        except (OSError, ValueError, RuntimeError):
            state.update(acquisition_status="blocked", processing_status="blocked")
            blockers.append("local_source_missing_unsafe_changed_or_over_limit")
    if workflow:
        try:
            resolve_workflow_reference(workflow)
            state["workflow_references"] = (workflow,)
        except (OSError, ValueError):
            blockers.append("workflow_reference_invalid")
    if ref:
        try:
            if not grant:
                raise PermissionError("Source grant required")
            if (
                (row.adapter == "c18_material" and ref.kind != "material")
                or (row.adapter == "offline_transcript" and ref.kind != "transcript")
                or row.adapter == "media_plan_only"
            ):
                raise ValueError("Evidence adapter mismatch")
            checked = media_evidence.verify(
                api.reviewed(binding) if ref.kind == "material" else binding,
                ref,
                grant,
                MediaLimits(),
                approvals=approvals,
            )
            if (
                row.parser is not None
                and checked.get("parser_revision") != row.parser.config_id
            ):
                raise ValueError(
                    "Parser configuration changed; retain old outputs and review a new workspace"
                )
            state.update(
                acquisition_status="verified",
                processing_status="completed",
                quality_status=checked["technical_quality"]
                if ref.kind == "material"
                else "verified_transcript",
                raw_sha256=checked["raw_sha256"],
                action="reuse_verified_result",
            )
        except (OSError, ValueError, RuntimeError):
            state.update(
                acquisition_status="blocked",
                processing_status="blocked",
                quality_status="failed",
            )
            blockers.append("existing_evidence_failed_hash_binding_config_or_quality")
    if row.selected and state["processing_status"] != "completed":
        if row.adapter == "media_plan_only":
            blockers.append(
                "media_requires_separate_existing_media_plan; no_download_or_whisper"
            )
        if "assignment_child_not_in_existing_c18_discovery_graph" in row.limitations:
            blockers.append("assignment_child_c18_adapter_not_integrated")
        if (
            request.mode in {"process_existing", "plan"}
            and state["acquisition_status"] != "verified"
        ):
            blockers.append("verified_local_input_required")
        if request.mode == "approved_acquisition":
            try:
                api.approval(binding, approvals, "download")
            except PermissionError:
                missing.append("source_download_approval")
            blockers.append(
                "approved_acquisition_is_plan_only; use_existing_source_specific_pipeline"
            )
        if request.mode != "discovery_only":
            required = (
                request.limits.reserve_bytes
                + request.limits.total_raw_bytes * 4
                + 512 * 1048576
                + 16 * 1048576
            )
            if request.available_bytes is None or request.available_bytes < required:
                blockers.append(
                    "capacity_unknown_or_insufficient_including_5gib_reserve"
                )
            if (
                request.available_memory_mb is None
                or request.available_memory_mb < request.limits.memory_mb
            ):
                blockers.append("memory_capacity_unknown_or_insufficient")
            if not request.existing_worker_confirmed:
                blockers.append("existing_single_worker_and_queue_limits_not_confirmed")
        if not blockers and not missing:
            state["action"] = (
                "ready_transcript_import"
                if row.adapter == "offline_transcript"
                else "ready_c18_submission"
            )
        else:
            state["action"] = "blocked"
    if row.selected and row.acquisition_policy != "manual_only":
        steps = []
        if request.mode == "approved_acquisition":
            steps.extend(
                (
                    "require_source_specific_download_approval",
                    "existing_serial_acquisition_after_separate_operator_action",
                )
            )
        if row.adapter == "c18_material":
            steps.extend(
                (
                    "verify_local_source_hash",
                    "prepare_existing_one_source_c18_bundle",
                    "existing_controller_preview",
                    "operator_submit_to_existing_single_worker",
                )
            )
        elif row.adapter == "offline_transcript":
            steps.extend(
                ("verify_local_transcript_hash", "existing_offline_transcript_adapter")
            )
        elif row.adapter == "media_plan_only":
            steps.append("existing_media_plan_with_explicit_purpose_and_evidence")
        if state["processing_status"] == "completed":
            steps = ["verify_existing_result", "reuse_without_processing"]
        state["planned_steps"] = tuple(steps)
    state.update(
        blockers=tuple(dict.fromkeys(blockers)), missing_approvals=tuple(missing)
    )
    if missing and state["acquisition_status"] == "not_requested":
        state["acquisition_status"] = "approval_required"
    return WeekResource.model_validate(state)


def plan_week(request, approvals=None):
    """Inventory/plan only; no auto-dispatch, acquisition or recursive discovery."""
    request_type = (
        ProfiledWeekRequest if isinstance(request, ProfiledWeekRequest) else WeekRequest
    )
    request = request_type.model_validate_json(request.model_dump_json())
    approvals = (
        api.Approvals.model_validate_json(approvals.model_dump_json())
        if approvals
        else api.Approvals()
    )
    rows, snapshots, native = _inventory(request)
    known = {r.material_id for r in rows}
    named = set(request.material_ids)
    if named - known:
        raise ValueError("Selected material is not proven in this week")
    if any(
        e.material_id not in known
        for entries in (
            request.local_sources,
            request.evidence,
            request.workflow_references,
        )
        for e in entries
    ):
        raise ValueError("Local evidence refers to an unknown/out-of-week material")
    scope = named or (
        {r.material_id for r in rows}
        if isinstance(request, ProfiledWeekRequest)
        and request.selection in {"all", "complete"}
        and request.mode != "discovery_only"
        else (
            {r.material_id for r in rows if r.category in request.material_types}
            if request.mode != "discovery_only"
            else set()
        )
    )
    if named and any(
        r.material_id in named
        and r.category not in request.material_types
        and r.acquisition_policy != "manual_only"
        for r in rows
    ):
        raise ValueError("Material scope contradicts selected types")
    result = []
    for row in rows:
        row = row.model_copy(update={"selected": row.material_id in scope})
        if request.mode != "discovery_only":
            row = _observations(row, request, approvals)
        elif row.acquisition_policy == "manual_only":
            row = row.model_copy(
                update={
                    "action": "reference_only",
                    "acquisition_status": "manual_required",
                }
            )
        if (
            row.selected
            and len(scope) > request.limits.max_materials
            and row.processing_status != "completed"
        ):
            row = row.model_copy(
                update={
                    "action": "blocked",
                    "blockers": (
                        *row.blockers,
                        "selected_scope_exceeds_material_limit",
                    ),
                }
            )
        result.append(row)
    total_raw = sum(r.raw_bytes or 0 for r in result if r.selected)
    if total_raw > request.limits.total_raw_bytes:
        result = [
            r.model_copy(
                update={
                    "action": "blocked",
                    "blockers": (*r.blockers, "total_raw_byte_limit"),
                }
            )
            if r.selected and r.processing_status != "completed"
            else r
            for r in result
        ]
    gaps = [
        "live_coverage_not_checked",
        "private_archives_and_running_pilot_not_scanned",
    ]
    observed_urls = {s.original_url for s in snapshots}
    for row in result:
        if (
            row.binding.role in {"notes", "problem_set"}
            and row.binding.variant_id is None
            and row.binding.original_url not in observed_urls
        ):
            gaps.append("source_snapshot_not_provided:" + row.resource_id)
    section = (
        next(s for s in request.profile.sections if s.key == request.week)
        if isinstance(request, ProfiledWeekRequest)
        else None
    )
    expected_tasks = (
        section.expected_tasks
        if section
        else (EXPECTED_TASKS if request.week == "0" else ())
    )
    if expected_tasks:
        titles = {
            r.title.casefold()
            for r in result
            if r.parent_resource_ids and r.binding.role == "problem_set"
        }
        gaps.extend(
            "task_not_proven:" + name
            for name in expected_tasks
            if name.casefold() not in titles
        )
    if section:
        roles = {r.binding.role for r in result}
        gaps.extend(
            "required_role_missing:" + role.value
            for role in section.required_roles
            if role.value not in roles
        )
    selected = [r for r in result if r.selected]
    complete = bool(selected) and all(
        r.processing_status == "completed"
        and not r.blockers
        and not r.missing_approvals
        for r in selected
    )
    counts = week_counts(result, gaps)
    report_type = ProfiledWeekReport if section else WeekReport
    extra = (
        {"profile_sha256": fingerprint(request.profile.model_dump(mode="json"))}
        if section
        else {}
    )
    return report_type(
        **extra,
        course_id=request.course_id,
        week=request.week,
        mode=request.mode,
        request_sha256=fingerprint(request.model_dump(mode="json")),
        manifest_sha256=api.sha(read_file(request.manifest)),
        snapshots=snapshots,
        resources=tuple(result),
        scope_material_ids=tuple(r.material_id for r in selected),
        counts=counts,
        gaps=tuple(gaps),
        limits=request.limits,
        scope_processing_complete=complete,
        technical_workflow_complete=complete,
    )


def prepare_material_batches(request, approvals):
    """Recheck inputs and return one-source batches for the existing C18 path.

    No controller call and no write. Transcript rows use the existing transcript
    adapter separately. New assignment-child IDs stay blocked until that adapter
    can reproduce their graph inside the immutable C18 bundle.
    """
    report = plan_week(request, approvals)
    batches = []
    for row in report.resources:
        if row.action != "ready_c18_submission":
            continue
        category, policy, adapter, _ = routing(row.binding, request.limits)
        if (
            category not in {"html", "pdf"}
            or policy != "approval_required"
            or adapter != "c18_material"
        ):
            raise PermissionError(
                "Only approved document material batches are supported"
            )
        batch = api.plan(
            request.manifest,
            [request.course_id],
            [row.material_id],
            synthetic=request.source_origin == "synthetic",
        )
        batches.append(batch.model_copy(update={"max_bytes": request.limits.max_bytes}))
    return report, tuple(batches)


def prepare_transcript_batches(request, approvals):
    """Bounded existing SRT/TXT adapter inputs; no import or queue side effects."""
    from src.tools_materials.capacity import CapacityLimits

    report = plan_week(request, approvals)
    batches = []
    for row in report.resources:
        if row.action != "ready_transcript_import":
            continue
        if (
            not transcripts.supported(row.binding)
            or routing(row.binding, request.limits)[0] != "transcript"
        ):
            raise PermissionError("Only bound SRT/TXT inputs are supported")
        batch = api.plan(
            request.manifest,
            [request.course_id],
            [row.material_id],
            synthetic=request.source_origin == "synthetic",
        )
        batch = batch.model_copy(update={"max_bytes": request.limits.max_bytes})
        transcripts.checked(
            batch,
            CapacityLimits(
                reserve_bytes=request.limits.reserve_bytes,
                archive_bytes=64 * 1048576,
                max_materials=1,
            ),
        )
        batches.append(batch)
    return report, tuple(batches)
