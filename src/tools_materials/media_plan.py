"""Deterministic F0-F6 proposals, not an executable acquisition pipeline.

Never imports yt-dlp, Whisper, ffmpeg, inference providers or legacy URL fallback.
Unknown adequacy/access/technical failure stops escalation rather than authorizing it.
"""

import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import fingerprint
from src.job_control.operations import private
from src.model_materials.materials import MaterialResource
from src.model_materials.media_plan import MediaRequest
from src.tools_materials import batch as api
from src.tools_materials import media_evidence, transcripts
from src.tools_materials.inventory import catalog
from src.tools_materials.processing import make_plan, parser_for
from src.tools_materials.storage import artifact_root


def bindings(request):
    graph = make_plan(
        request.manifest, include_code_indexes=request.include_code_indexes
    )
    selected = [
        b
        for b in graph.materials
        if b.resource.course_id == request.course_id
        and request.lecture_id in b.lecture_ids
    ]
    lectures = [
        b
        for b in selected
        if b.source_id == request.lecture_id and b.role == "lecture_video"
    ]
    if len(lectures) != 1 or any(
        b.lecture_ids != (request.lecture_id,) for b in selected
    ):
        raise ValueError("Missing or ambiguous lecture binding")
    subject = request.subject_id or request.lecture_id
    if subject != request.lecture_id:
        shorts = [b for b in selected if b.source_id == subject and b.role == "short"]
        if len(shorts) != 1:
            raise ValueError("Unknown Short subject")
        selected = [
            b
            for b in selected
            if b.source_id == subject or b.resource.parent_resource_id == subject
        ]
    result = []
    for binding in selected:
        result.append(
            binding.model_copy(update={"source_origin": request.source_origin})
        )
        for variant in binding.resource.variants:
            result.append(
                MaterialResource(
                    resource=binding.resource,
                    lecture_ids=binding.lecture_ids,
                    variant_id=variant.variant_id,
                    original_url=str(variant.original_url),
                    format=variant.format or "unknown",
                    language=variant.language,
                    role=binding.role,
                    source_origin=request.source_origin,
                )
            )
    if len(result) > 64:
        raise ValueError("Material/variant bound exceeded")
    return result


def adapter(binding):
    if binding.role in {"audio", "lecture_video"}:
        return "media_reference_only"
    if binding.role == "short":
        return "short_reference_only"
    if binding.format in {"py", "zip"}:
        from src.tools_materials.code_import import supported

        if supported(binding):
            return "b6_offline_code"
    if binding.format in {"srt", "vtt", "txt"} and binding.role in {
        "subtitles",
        "transcript",
    }:
        return (
            "b5_offline_transcript"
            if transcripts.supported(binding)
            else "standalone_transcript_import_only"
        )
    if (
        binding.role == "slides"
        and urlsplit(binding.original_url).hostname == "docs.google.com"
    ):
        return "presentation_export_permission_required"
    config, _status, _reason = parser_for(binding)
    return "existing_material" if config is not None else "unsupported_reference"


def stage_for(binding):
    if binding.role in {"subtitles", "transcript"}:
        return "F1"
    if binding.role in {"audio", "lecture_video"}:
        return "F5" if binding.role == "audio" else "F6"
    if adapter(binding) in {
        "presentation_export_permission_required",
        "short_reference_only",
    }:
        return "F3"
    return "F2"


def key(binding, request):
    variant = next(
        (v for v in binding.resource.variants if v.variant_id == binding.variant_id),
        None,
    )
    return (
        binding.language != request.policy.preferred_language,
        binding.role != "notes",
        {"srt": 0, "vtt": 1, "txt": 2, "html": 0, "pdf": 1}.get(binding.format, 9),
        bool(
            variant and variant.resolution != request.policy.preferred_video_resolution
        ),
        bool(variant and request.policy.prefer_sdr and variant.dynamic_range == "hdr"),
        binding.original_url,
        binding.material_id,
    )


def plan(request, approvals):
    request = MediaRequest.model_validate(request.model_dump(mode="json"))
    root = artifact_root(safe_path(request.resource_probe_root))
    private(root, directory=True)
    materials = bindings(request)
    by_id = {b.material_id: b for b in materials}
    for entries in (
        request.evidence,
        request.adequacy,
        request.unavailable,
        request.estimates,
    ):
        if {e.material_id for e in entries} - by_id.keys():
            raise ValueError(
                "Planning input references unknown/out-of-subject material"
            )
    evidence = {e.material_id: e for e in request.evidence}
    reviews = {e.material_id: e for e in request.adequacy}
    unavailable = {e.material_id: e for e in request.unavailable}
    estimates = {e.material_id: e for e in request.estimates}
    grants, observations, rows = {}, {}, []
    integrity_blocker = False
    for binding in materials:
        mid = binding.material_id
        row = dict(
            material_id=mid,
            source_id=binding.source_id,
            original_url=binding.original_url,
            variant_id=binding.variant_id,
            role=binding.role,
            format=binding.format,
            lecture_ids=list(binding.lecture_ids),
            language=binding.language,
            topic=binding.resource.title if binding.role == "short" else None,
            states=[],
            remote_reference=True,
            remote_availability="not_checked",
            adapter=adapter(binding),
            technically_processable=adapter(binding)
            in {"existing_material", "b5_offline_transcript", "b6_offline_code"},
            download_approved=False,
            process_approved=False,
            processed=False,
            verified=False,
            provenance="reference_only",
            times="unknown",
            duration_seconds=None,
            adequate_for_purpose=dict(text="unknown", visual="unknown"),
            human_quality="not_evaluated",
        )
        try:
            row["download_approved"] = api.approval(
                binding, approvals, "download"
            ).download
        except PermissionError:
            pass
        try:
            grant = api.approval(binding, approvals, "process")
            grants[mid] = grant
            row["approval_sha256"] = fingerprint(grant.model_dump(mode="json"))
            row.update(download_approved=grant.download, process_approved=True)
            row["states"].append("approved")
        except PermissionError:
            # A download flag alone is not a processing capability.
            pass
        if mid in evidence:
            row["receipt_sha256"] = evidence[mid].receipt_sha256
            try:
                if mid not in grants:
                    raise PermissionError("Current process approval missing")
                observed = media_evidence.verify(
                    binding,
                    evidence[mid],
                    grants[mid],
                    request.limits,
                    approvals=approvals,
                )
                observations[mid] = observed
                row.update(observed)
                row["states"] += ["available_local", "verified"]
                if row["technically_processable"] and observed["processed"]:
                    row["states"].append("ready_for_processing")
            except (ValueError, OSError, RuntimeError) as error:
                integrity_blocker = True
                row["states"].append("blocked")
                row["evidence_error"] = type(error).__name__
        else:
            row["states"].append("missing")
        if mid in reviews:
            review = reviews[mid]
            if (
                mid not in observations
                or review.raw_sha256 != observations[mid]["raw_sha256"]
                or review.purpose != request.purpose
            ):
                raise ValueError(
                    "Adequacy is not bound to verified bytes/current purpose"
                )
            row["adequate_for_purpose"] = dict(text=review.text, visual=review.visual)
        if row["adapter"] in {
            "unsupported_reference",
            "standalone_transcript_import_only",
            "short_reference_only",
            "presentation_export_permission_required",
        }:
            row["states"].append("unsupported")
        rows.append(row)
    row_by_id = {r["material_id"]: r for r in rows}
    needed = {
        d
        for d, value in (("text", request.need_text), ("visual", request.need_visual))
        if value
    }
    reused = []
    for binding in sorted(materials, key=lambda b: key(b, request)):
        row = row_by_id[binding.material_id]
        filled = {
            d
            for d in needed
            if row["adequate_for_purpose"][d] == "adequate"
            and (d != "visual" or row.get("visual_evidence_available"))
        }
        if filled and row.get("verified") and row.get("processed"):
            needed -= filled
            reused.append(binding.material_id)
    stages = [
        dict(
            stage="F0",
            status="verified" if reused else "missing",
            reason="verified_purpose_bound_reuse"
            if reused
            else "no_sufficient_verified_local_artifacts",
        )
    ]
    selected, reason, selected_ids = (
        ("F0", "purpose_satisfied_by_verified_local_artifacts", list(reused))
        if not needed
        else (None, None, list(reused))
    )
    blocked = integrity_blocker
    if integrity_blocker:
        reason = "local_evidence_integrity_or_permission_blocker"
        selected = None
    failure = any(
        e.reason in {"access_denied", "technical_failure"} for e in request.unavailable
    )
    if failure and needed:
        blocked, selected, reason = (
            True,
            None,
            "access_or_technical_failure_requires_new_operator_decision",
        )
    for stage in ("F1", "F2", "F3", "F4", "F5", "F6"):
        if selected is not None or blocked:
            stages.append(
                dict(
                    stage=stage,
                    status="not_required" if not needed and not blocked else "blocked",
                    reason="purpose_satisfied"
                    if not needed and not blocked
                    else "earlier_stage_pending",
                )
            )
            continue
        candidates = []
        for binding in materials:
            mid = binding.material_id
            if mid in unavailable:
                continue
            own = stage_for(binding)
            if stage == "F1" and "text" not in needed:
                continue
            if stage == "F5" and "text" not in needed:
                continue  # Audio cannot close a visual-only gap.
            if stage in {"F4", "F5", "F6"}:
                if binding.role not in {"audio", "lecture_video"}:
                    continue
                if "text" not in needed and binding.role != "lecture_video":
                    continue
                if stage == "F4" and mid in observations:
                    candidates.append(binding)
                elif stage == own and mid not in observations:
                    candidates.append(binding)
                continue
            if own != stage:
                continue
            row = row_by_id[mid]
            if all(row["adequate_for_purpose"][d] == "inadequate" for d in needed):
                continue
            candidates.append(binding)
        if not candidates:
            stages.append(
                dict(
                    stage=stage,
                    status="missing",
                    reason="no_suitable_candidate_in_declared_reference_scope",
                )
            )
            continue
        binding = sorted(
            candidates,
            key=lambda b: (
                b.role != "audio"
                if stage == "F4" and "visual" not in needed
                else False,
                key(b, request),
            ),
        )[0]
        mid = binding.material_id
        row = row_by_id[mid]
        selected, selected_ids = stage, [*reused, mid]
        reason = "earlier_known_alternatives_exhausted_or_not_applicable"
        blockers = []
        if not row["process_approved"]:
            blockers.append("source_process_approval_missing")
        if mid not in observations and not row["download_approved"]:
            blockers.append("source_download_approval_missing")
        if mid in observations and stage != "F4":
            blockers.append("purpose_adequacy_review_pending")
        if stage in {"F1", "F2", "F3"}:
            if not row["technically_processable"]:
                blockers.append("bounded_adapter_or_export_permission_missing")
            if binding.format == "zip" and mid not in observations:
                blockers.append(
                    "zip_requires_explicit_offline_input_and_member_mapping"
                )
        else:
            estimate = estimates.get(mid)
            maximum = (
                request.limits.audio_bytes
                if binding.role == "audio"
                else request.limits.video_bytes
            )
            if estimate is None:
                blockers.append("media_size_duration_estimate_missing")
            else:
                row["resource_estimate"] = estimate.model_dump(
                    mode="json", exclude={"estimate_reference"}
                )
                if (
                    estimate.bytes > maximum
                    or estimate.duration_seconds > request.limits.duration_seconds
                ):
                    blockers.append("media_size_or_duration_limit")
                if row.get("bytes", 0) > estimate.bytes:
                    blockers.append("local_bytes_exceed_estimate")
                required = 2 * estimate.bytes + request.limits.scratch_bytes
                if (
                    shutil.disk_usage(root).free
                    < request.limits.reserve_bytes + required
                ):
                    blockers.append("media_capacity_reserve")
                if any(
                    w.end > estimate.duration_seconds for w in request.visual_windows
                ):
                    blockers.append("visual_window_outside_declared_duration")
            if "text" in needed and not request.policy.allow_transcription:
                blockers.append("transcription_not_approved")
            # Legacy methods have no safe C26 bounded process/receipt wrapper yet.
            blockers.append("bounded_media_execution_adapter_missing")
            row["component_reference"] = (
                "src.model_transcribe.provider_transcript.FasterWhisperProvider.transcribe"
                if "text" in needed
                else "src.tools_transcribe.extract_video.prepare_local_visual_sections"
            )
            row["proposed_action"] = (
                "transcribe_local_media"
                if stage == "F4" and "text" in needed
                else "plan_visual_windows"
                if stage == "F4"
                else "propose_audio_download"
                if stage == "F5"
                else "propose_video_download"
            )
        blocked = bool(blockers)
        row["states"].append("blocked" if blocked else "approved")
        stages.append(
            dict(
                stage=stage,
                status="blocked" if blocked else "approved",
                material_id=mid,
                reason=reason,
                blockers=blockers,
            )
        )
    if selected is None and needed and not blocked:
        blocked = True
        reason = "no_suitable_candidate_in_declared_reference_scope"
    if "visual" in needed:
        for row in rows:
            if row["material_id"] in selected_ids:
                row["states"].append("requires_visual_context")
    snapshot = api.plan(
        request.manifest,
        [request.course_id],
        [request.lecture_id],
        synthetic=request.source_origin == "synthetic",
    )
    refs = catalog(request.manifest)["references"]
    report = dict(
        schema_version=1,
        planner_version="media_last_v1",
        scope="known_snapshot_references_only",
        course_id=request.course_id,
        lecture_id=request.lecture_id,
        subject_id=request.subject_id or request.lecture_id,
        purpose=request.purpose,
        source_origin=request.source_origin,
        request_sha256=fingerprint(request.model_dump(mode="json")),
        snapshot_files=snapshot.files,
        selected_strategy=selected,
        selected_materials=selected_ids,
        actually_used_materials=reused,
        missing_content=sorted(needed),
        reason=reason,
        stages=stages,
        materials=rows,
        blocked=blocked,
        coverage=dict(
            text="adequate_for_declared_purpose"
            if request.need_text and "text" not in needed
            else "not_requested"
            if not request.need_text
            else "unresolved",
            visual="adequate_for_declared_purpose"
            if request.need_visual and "visual" not in needed
            else "not_requested"
            if not request.need_visual
            else "requires_visual_context",
            provenance="verified_local_only"
            if reused
            else "references_or_hash_bound_inputs",
            full_lecture_coverage=False,
            human_quality="not_evaluated",
        ),
        known_references=[
            r
            for r in refs
            if r["course_id"] == request.course_id
            and set(r["section_keys"]) & set(materials[0].resource.section_keys)
        ],
        unavailable=[
            e.model_dump(mode="json", exclude={"decision_reference"})
            for e in request.unavailable
        ],
        referenced_transcript_languages=sorted(
            {
                b.language
                for b in materials
                if b.role in {"subtitles", "transcript"} and b.language
            }
        ),
        available_transcript_languages=sorted(
            {
                r["language"]
                for r in rows
                if r["role"] in {"subtitles", "transcript"}
                and r["verified"]
                and r["language"]
            }
        ),
        media_limits=request.limits.model_dump(mode="json"),
        visual_plan=dict(
            windows=[w.model_dump() for w in request.visual_windows],
            max_frames=request.limits.max_frames,
            execution_supported=False,
            note="source time references only; no frames acquired",
        ),
        execution_supported=False,
        knowledge_fact_verified=False,
        network_requests=0,
        media_operations=0,
        transcription_operations=0,
    )
    report["implementation_sha256"] = fingerprint(
        {
            name: api.sha(read_file(Path(path)))
            for name, path in (
                ("planner", __file__),
                ("evidence", media_evidence.__file__),
                ("contract", sys.modules[MediaRequest.__module__].__file__),
            )
        }
    )
    return dict(report=report, sha256=fingerprint(report))


def check_previous(previous, current):
    if (
        set(previous) != {"report", "sha256"}
        or previous["sha256"] != fingerprint(previous["report"])
        or previous["sha256"] != current["sha256"]
    ):
        raise ValueError("Previous plan tampered or stale; explicit replan required")
