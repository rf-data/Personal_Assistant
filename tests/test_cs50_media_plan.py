"""Synthetic media-last integration, real B5/C10 evidence; no media processing."""

import json
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import cs50_batch as cli
from scripts.cs50_workflow_demo import inputs as demo_inputs
from src.model_materials.media_plan import (
    Adequacy,
    EvidenceRef,
    MediaEstimate,
    MediaLimits,
    MediaRequest,
    TimeWindow,
    Unavailability,
)
from src.tools_materials import batch as api
from src.tools_materials import media_plan as lane
from src.tools_materials import transcripts
from src.tools_materials.capacity import MIB, CapacityLimits
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.processing import MaterialProcessor, make_plan


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Network/media processing forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    import subprocess

    monkeypatch.setattr(subprocess, "Popen", forbidden)


def grant(binding, raw=None, *, process=True, download=False):
    refs = {
        name: "synthetic-operator-evidence"
        for name in api.SourceApproval.model_fields
        if name.endswith("_reference")
    }
    return api.SourceApproval(
        material_id=binding.material_id,
        source_id=binding.source_id,
        course_id=binding.resource.course_id,
        original_url=binding.original_url,
        expected_sha256=api.sha(raw) if raw is not None else None,
        process=process,
        download=download,
        **refs,
    )


@pytest.fixture
def env(tmp_path, monkeypatch, private_umask):
    tmp_path.chmod(0o700)
    monkeypatch.setattr(
        "shutil.disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3)
    )
    source = tmp_path / "snapshots"
    demo_inputs(source)
    page = source / "cs50_python/week0.html"
    extra = '<li>Audio<ul><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.mp3">MP3</a></li></ul></li>'
    extra += '<li>Subtitles<ul><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt">SRT</a></li></ul></li>'
    extra += '<li>Slides<ul><li><a href="https://docs.google.com/presentation/d/synthetic/edit">Google Slides</a></li></ul></li>'
    page.write_text(
        page.read_text().replace(
            "</ul></li></ul></main>", extra + "</ul></li></ul></main>"
        )
    )
    data = json.loads((source / "manifest.json").read_bytes())
    for p in data["courses"][0]["pages"]:
        p["sha256"] = api.sha((source / p["file"]).read_bytes())
    manifest = source / "manifest.json"
    manifest.write_text(json.dumps(data))
    graph = make_plan(manifest)
    bindings = [
        b.model_copy(update={"source_origin": "synthetic"}) for b in graph.materials
    ]
    lecture = next(b for b in bindings if b.role == "lecture_video")
    request = MediaRequest(
        manifest=manifest,
        course_id="cs50_python",
        lecture_id=lecture.source_id,
        purpose="synthetic text purpose",
        resource_probe_root=tmp_path,
        source_origin="synthetic",
    )
    rows = lane.bindings(request)
    srt = next(b for b in rows if b.format == "srt")
    audio = next(b for b in rows if b.format == "mp3")
    srt_raw = b"17\n00:00:01,000 --> 00:00:03,000\nFirst\n\n42\n00:00:02,000 --> 00:00:04,000\nSecond\n"
    media_raw = b"synthetic opaque media bytes; not a decodable audio fixture"
    grants = [
        grant(
            b,
            srt_raw
            if b.material_id == srt.material_id
            else media_raw
            if b.material_id == audio.material_id
            else None,
        )
        for b in rows
    ]
    approvals = api.Approvals(sources=tuple(grants))
    batch = api.plan(manifest, ["cs50_python"], [srt.source_id], synthetic=True)
    batch_path = tmp_path / "transcript-batch.json"
    batch_path.write_text(
        json.dumps(
            dict(
                batch=batch.model_dump(mode="json"),
                sha256=api.fingerprint(batch.model_dump(mode="json")),
            )
        )
    )
    original = tmp_path / "official.srt"
    original.write_bytes(srt_raw)
    archive = tmp_path / "transcripts"
    limits = CapacityLimits(
        reserve_bytes=5 * 1024**3, archive_bytes=64 * MIB, max_materials=8
    )
    assert (
        transcripts.run(
            batch,
            archive,
            approvals,
            {srt.source_id: original},
            action="import",
            limits=limits,
        )["processed_materials"]
        == 1
    )
    receipt_path = archive / srt.material_id.split(":")[-1] / "receipt.json"
    ref = EvidenceRef(
        material_id=srt.material_id,
        kind="transcript",
        workspace=archive,
        batch=batch_path,
        receipt_sha256=api.sha(receipt_path.read_bytes()),
    )
    media_dir = tmp_path / "local-media"
    media_dir.mkdir(mode=0o700)
    (media_dir / "audio.mp3").write_bytes(media_raw)
    return SimpleNamespace(
        request=request,
        bindings=rows,
        srt=srt,
        audio=audio,
        lecture=lecture,
        approvals=approvals,
        transcript=ref,
        receipt_path=receipt_path,
        root=tmp_path,
        media_dir=media_dir,
        media_raw=media_raw,
        limits=limits,
    )


def assess(env, *, text="adequate", visual="unknown"):
    raw_hash = next(
        g.expected_sha256
        for g in env.approvals.sources
        if g.material_id == env.srt.material_id
    )
    return Adequacy(
        material_id=env.srt.material_id,
        raw_sha256=raw_hash,
        purpose=env.request.purpose,
        text=text,
        visual=visual,
        decision_reference="synthetic-purpose-review",
    )


def declines(env):
    return tuple(
        Unavailability(
            material_id=b.material_id,
            reason="not_applicable",
            decision_reference="synthetic-reviewed-alternative",
        )
        for b in env.bindings
        if lane.stage_for(b) in {"F1", "F2", "F3"}
    )


def run(env, **updates):
    request = env.request.model_copy(update=updates)
    return lane.plan(request, env.approvals)["report"]


def test_verified_official_local_transcript_avoids_all_media_and_repeat_is_readonly(
    env,
):
    before = {
        p.relative_to(env.transcript.workspace).as_posix(): p.read_bytes()
        for p in env.transcript.workspace.rglob("*")
        if p.is_file()
    }
    request = env.request.model_copy(
        update={"evidence": (env.transcript,), "adequacy": (assess(env),)}
    )
    first = lane.plan(request, env.approvals)
    second = lane.plan(request, env.approvals)
    assert first == second
    lane.check_previous(first, second)
    report = first["report"]
    assert report["selected_strategy"] == "F0" and not report["blocked"]
    assert report["missing_content"] == []
    assert all(s["status"] == "not_required" for s in report["stages"][1:])
    assert (
        report["media_operations"]
        == report["network_requests"]
        == report["transcription_operations"]
        == 0
    )
    assert (
        not report["execution_supported"]
        and not report["coverage"]["full_lecture_coverage"]
    )
    row = next(
        r for r in report["materials"] if r["material_id"] == env.srt.material_id
    )
    assert row["times"] == "source_cues" and row["duration_seconds"] == 4
    assert str(env.root) not in json.dumps(report)
    assert before == {
        p.relative_to(env.transcript.workspace).as_posix(): p.read_bytes()
        for p in env.transcript.workspace.rglob("*")
        if p.is_file()
    }


def test_unknown_transcript_adequacy_blocks_instead_of_falling_through(env):
    report = run(env, evidence=(env.transcript,))
    assert report["selected_strategy"] == "F1" and report["blocked"]
    assert report["missing_content"] == ["text"]
    assert report["stages"][1]["blockers"] == ["purpose_adequacy_review_pending"]


def test_remote_official_transcript_proposed_before_media(env):
    env.approvals = api.Approvals(
        sources=tuple(
            g.model_copy(update={"download": True}) for g in env.approvals.sources
        )
    )
    report = run(env)
    assert report["selected_strategy"] == "F1" and not report["blocked"]
    assert report["actually_used_materials"] == [] and report["missing_content"] == [
        "text"
    ]
    row = next(
        r for r in report["materials"] if r["material_id"] == env.srt.material_id
    )
    assert "ready_for_processing" not in row["states"]  # No verified remote bytes yet.


def test_missing_transcript_local_audio_proposes_existing_provider_only(env):
    ref = EvidenceRef(
        material_id=env.audio.material_id,
        kind="media",
        workspace=env.media_dir,
        relative_path="audio.mp3",
    )
    estimate = MediaEstimate(
        material_id=env.audio.material_id,
        bytes=1000,
        duration_seconds=20,
        estimate_reference="synthetic-size-estimate",
    )
    report = run(
        env,
        evidence=(ref,),
        unavailable=declines(env),
        estimates=(estimate,),
        policy=env.request.policy.model_copy(update={"allow_transcription": True}),
    )
    assert report["selected_strategy"] == "F4" and report["blocked"]
    stage = next(s for s in report["stages"] if s["stage"] == "F4")
    assert stage["blockers"] == ["bounded_media_execution_adapter_missing"]
    row = next(
        r for r in report["materials"] if r["material_id"] == env.audio.material_id
    )
    assert row["component_reference"].endswith("FasterWhisperProvider.transcribe")
    assert row["proposed_action"] == "transcribe_local_media"


def test_complete_text_does_not_hide_visual_gap(env):
    report = run(
        env, evidence=(env.transcript,), adequacy=(assess(env),), need_visual=True
    )
    assert report["coverage"]["text"] == "adequate_for_declared_purpose"
    assert report["coverage"]["visual"] == "requires_visual_context"
    assert report["missing_content"] == ["visual"]
    assert all(s.get("material_id") != env.audio.material_id for s in report["stages"])


@pytest.mark.parametrize("role,stage", [("audio", "F5"), ("lecture_video", "F6")])
def test_unapproved_remote_media_never_downloads(env, role, stage):
    unavailable = list(declines(env))
    if role == "lecture_video":
        unavailable.extend(
            Unavailability(
                material_id=b.material_id,
                reason="not_applicable",
                decision_reference="audio-will-not-fill-purpose",
            )
            for b in env.bindings
            if b.role == "audio"
        )
    report = run(env, unavailable=tuple(unavailable))
    assert report["selected_strategy"] == stage and report["blocked"]
    selected = next(s for s in report["stages"] if s["stage"] == stage)
    assert "source_download_approval_missing" in selected["blockers"]
    assert report["network_requests"] == report["media_operations"] == 0


def test_video_permission_does_not_bypass_capacity(env, monkeypatch):
    env.approvals = api.Approvals(
        sources=tuple(
            g.model_copy(update={"download": True}) for g in env.approvals.sources
        )
    )
    unavailable = (
        *declines(env),
        *(
            Unavailability(
                material_id=b.material_id,
                reason="not_applicable",
                decision_reference="visual-only",
            )
            for b in env.bindings
            if b.role == "audio"
        ),
    )
    estimate = MediaEstimate(
        material_id=env.lecture.material_id,
        bytes=1000,
        duration_seconds=20,
        estimate_reference="synthetic-estimate",
    )
    monkeypatch.setattr(
        "shutil.disk_usage", lambda _: SimpleNamespace(free=5 * 1024**3)
    )
    report = run(
        env,
        unavailable=unavailable,
        estimates=(estimate,),
        need_visual=True,
        policy=env.request.policy.model_copy(update={"allow_transcription": True}),
    )
    stage = next(s for s in report["stages"] if s["stage"] == "F6")
    assert "media_capacity_reserve" in stage["blockers"]


@pytest.mark.parametrize("failure", ["access_denied", "technical_failure"])
def test_access_and_download_errors_never_authorize_alternate_downloader(env, failure):
    bad = Unavailability(
        material_id=env.srt.material_id,
        reason=failure,
        decision_reference="synthetic-failure",
    )
    report = run(env, unavailable=(bad,))
    assert report["blocked"] and report["selected_strategy"] is None
    assert (
        report["reason"] == "access_or_technical_failure_requires_new_operator_decision"
    )


@pytest.mark.parametrize("target", ["receipt", "raw", "payload", "symlink", "grant"])
def test_tampered_or_revoked_evidence_stops_all_escalation(env, target):
    if target == "grant":
        env.approvals = api.Approvals()
    elif target == "symlink":
        raw = env.receipt_path.parent / "source.srt"
        raw.unlink()
        raw.symlink_to(env.root / "official.srt")
    else:
        path = (
            env.receipt_path
            if target == "receipt"
            else env.receipt_path.parent
            / ("source.srt" if target == "raw" else "transcript.json")
        )
        path.write_bytes(path.read_bytes() + b" ")
    report = run(env, evidence=(env.transcript,))
    assert report["blocked"] and report["selected_strategy"] is None
    assert report["reason"] == "local_evidence_integrity_or_permission_blocker"


def test_wrong_purpose_hash_lecture_unknown_versions_and_limits(env):
    for update in (
        {"lecture_id": "foreign"},
        {"schema_version": 2},
        {"limits": MediaLimits().model_copy(update={"concurrent_jobs": 2})},
    ):
        with pytest.raises(ValueError):
            run(env, **update)
    for review in (
        assess(env).model_copy(update={"purpose": "another-purpose"}),
        assess(env).model_copy(update={"raw_sha256": "0" * 64}),
    ):
        with pytest.raises(ValueError):
            run(env, evidence=(env.transcript,), adequacy=(review,))
    with pytest.raises(ValueError):
        TimeWindow(start=30, end=5)
    with pytest.raises(ValueError):
        TimeWindow(start=0, end=61)


def test_existing_html_material_is_checked_by_actual_quality_handoff(env):
    binding = next(b for b in env.bindings if b.role == "notes")
    raw = b"<main><h1>Synthetic heading</h1><pre><code>  x = 1\r\n</code></pre></main>"
    original = env.root / "notes.html"
    original.write_bytes(raw)
    archive = env.root / "materials"
    downloader = MaterialDownloader(archive, max_bytes=MIB)
    downloader.obtain(binding, execute=True, local_file=original)
    MaterialProcessor(archive).parse(binding, execute=True)
    plan_path = env.root / "material-plan.json"
    model = make_plan(env.request.manifest)
    model = model.model_copy(
        update={
            "materials": tuple(
                b.model_copy(update={"source_origin": "synthetic"})
                for b in model.materials
            )
        }
    )
    plan_path.write_text(model.model_dump_json(indent=2))
    _raw_path, receipt_path = downloader.paths(binding)
    env.approvals = api.Approvals(
        sources=tuple(
            grant(binding, raw) if g.material_id == binding.material_id else g
            for g in env.approvals.sources
        )
    )
    evidence = EvidenceRef(
        material_id=binding.material_id,
        kind="material",
        workspace=archive,
        plan=plan_path,
        receipt_sha256=api.sha(receipt_path.read_bytes()),
    )
    review = Adequacy(
        material_id=binding.material_id,
        raw_sha256=api.sha(raw),
        purpose=env.request.purpose,
        text="adequate",
        decision_reference="synthetic-review",
    )
    report = run(env, evidence=(evidence,), adequacy=(review,))
    assert report["selected_strategy"] == "F0"
    row = next(
        r for r in report["materials"] if r["material_id"] == binding.material_id
    )
    assert (
        row["technical_quality"] == "passed_with_warnings"
        and row["human_quality"] == "not_evaluated"
    )


def test_cli_no_overwrite_and_previous_plan_integrity(env, capsys):
    env.request = env.request.model_copy(
        update={"evidence": (env.transcript,), "adequacy": (assess(env),)}
    )
    for name, model in (
        ("request", env.request),
        ("approvals", env.approvals),
        ("limits", env.limits),
    ):
        (env.root / f"{name}.json").write_text(model.model_dump_json())
    output = env.root / "plan.json"
    args = ["media-plan", "--output", str(output)]
    for name in ("request", "approvals", "limits"):
        args += ["--" + name, str(env.root / f"{name}.json")]
    assert cli.main(args) == 0
    current = json.loads(capsys.readouterr().out)
    before = output.read_bytes()
    assert cli.main(args) == 2
    assert before == output.read_bytes()
    capsys.readouterr()
    lane.check_previous(current, lane.plan(env.request, env.approvals))
    current["report"]["blocked"] = True
    with pytest.raises(ValueError):
        lane.check_previous(current, lane.plan(env.request, env.approvals))


def test_versioned_week_zero_shorts_presentations_variants_and_scope(tmp_path):
    tmp_path.chmod(0o700)
    manifest = (
        Path(__file__).resolve().parents[1] / "docs/course_sources/cs50/manifest.json"
    )
    graph = make_plan(manifest)
    lecture = next(
        b
        for b in graph.materials
        if b.resource.course_id == "cs50_python"
        and b.role == "lecture_video"
        and b.resource.section_keys == ("0",)
    )
    request = MediaRequest(
        manifest=manifest,
        course_id="cs50_python",
        lecture_id=lecture.source_id,
        purpose="metadata only",
        resource_probe_root=tmp_path,
    )
    report = lane.plan(request, api.Approvals())["report"]
    shorts = [r for r in report["materials"] if r["role"] == "short"]
    assert {r["topic"] for r in shorts} == {
        "Visual Studio Code for CS50",
        "Functions",
        "Variables",
        "Return Values",
        "Side Effects",
    }
    assert len({r["source_id"] for r in shorts}) == 5
    assert all(
        r["adapter"] == "short_reference_only" and not r["technically_processable"]
        for r in shorts
    )
    slides = [r for r in report["materials"] if "docs.google.com" in r["original_url"]]
    assert (
        len(slides) == 1
        and slides[0]["adapter"] == "presentation_export_permission_required"
    )
    variant_ids = [r["variant_id"] for r in report["materials"] if r["variant_id"]]
    assert len(variant_ids) == 8
    assert report["selected_strategy"] == "F1" and report["blocked"]
    subject_request = request.model_copy(update={"subject_id": shorts[0]["source_id"]})
    subject = lane.plan(subject_request, api.Approvals())["report"]
    assert len(subject["materials"]) == 1  # Lecture transcript cannot satisfy a Short.
    assert subject["missing_content"] == ["text"]


def test_deterministic_variant_choice_does_not_depend_on_enumeration(env, monkeypatch):
    from src.model_discovery.cs50 import MediaVariant
    from src.model_materials.materials import MaterialResource

    video = env.lecture
    variants = tuple(
        MediaVariant(
            original_url=f"https://cdn.cs50.net/python/2022/x/lectures/0/{resolution}.mp4",
            media_type="video",
            format="mp4",
            resolution=resolution,
            dynamic_range="sdr",
        )
        for resolution in ("720p", "360p")
    )
    resource = video.resource.model_copy(update={"variants": variants})
    options = [
        MaterialResource(
            resource=resource,
            lecture_ids=video.lecture_ids,
            variant_id=v.variant_id,
            original_url=str(v.original_url),
            format="mp4",
            role="lecture_video",
            source_origin="synthetic",
        )
        for v in variants
    ]
    base = [b for b in env.bindings if b.role != "lecture_video"]
    monkeypatch.setattr(lane, "bindings", lambda _: [*base, *options])
    unavailable = (
        *declines(env),
        Unavailability(
            material_id=env.audio.material_id,
            reason="not_applicable",
            decision_reference="synthetic-visual",
        ),
    )
    first = run(env, unavailable=unavailable, need_text=False, need_visual=True)
    monkeypatch.setattr(
        lane, "bindings", lambda _: [*reversed(base), *reversed(options)]
    )
    second = run(env, unavailable=unavailable, need_text=False, need_visual=True)
    assert (
        first["selected_materials"]
        == second["selected_materials"]
        == [options[1].material_id]
    )
    assert first["selected_strategy"] == second["selected_strategy"] == "F6"


def test_raw_media_and_transcript_cannot_claim_missing_visual_evidence(env):
    report = run(
        env,
        evidence=(env.transcript,),
        adequacy=(assess(env, visual="adequate"),),
        need_visual=True,
    )
    assert report["coverage"]["visual"] == "requires_visual_context"
    assert report["missing_content"] == ["visual"]
    ref = EvidenceRef(
        material_id=env.audio.material_id,
        kind="media",
        workspace=env.media_dir,
        relative_path="audio.mp3",
    )
    review = Adequacy(
        material_id=env.audio.material_id,
        raw_sha256=api.sha(env.media_raw),
        purpose=env.request.purpose,
        text="adequate",
        decision_reference="synthetic-review",
    )
    report = run(env, evidence=(ref,), adequacy=(review,), unavailable=declines(env))
    assert (
        report["actually_used_materials"] == []
        and report["coverage"]["text"] == "unresolved"
    )


@pytest.mark.parametrize(
    "problem", ["big", "long", "window", "estimate_missing", "transcription_unapproved"]
)
def test_separate_media_resource_limits(env, problem):
    ref = EvidenceRef(
        material_id=env.audio.material_id,
        kind="media",
        workspace=env.media_dir,
        relative_path="audio.mp3",
    )
    estimate = MediaEstimate(
        material_id=env.audio.material_id,
        bytes=65 * MIB if problem == "big" else 1000,
        duration_seconds=601 if problem == "long" else 20,
        estimate_reference="synthetic-estimate",
    )
    updates = dict(
        evidence=(ref,),
        unavailable=declines(env),
        estimates=() if problem == "estimate_missing" else (estimate,),
        policy=env.request.policy.model_copy(
            update={"allow_transcription": problem != "transcription_unapproved"}
        ),
    )
    if problem == "window":
        # Require video for a visual-only local source; range exceeds declared duration.
        video = env.lecture
        raw = b"synthetic opaque video"
        (env.media_dir / "video.mp4").write_bytes(raw)
        env.approvals = api.Approvals(
            sources=tuple(
                grant(video, raw) if g.material_id == video.material_id else g
                for g in env.approvals.sources
            )
        )
        updates.update(
            evidence=(
                EvidenceRef(
                    material_id=video.material_id,
                    kind="media",
                    workspace=env.media_dir,
                    relative_path="video.mp4",
                ),
            ),
            estimates=(
                MediaEstimate(
                    material_id=video.material_id,
                    bytes=1000,
                    duration_seconds=20,
                    estimate_reference="synthetic-estimate",
                ),
            ),
            visual_windows=(TimeWindow(start=10, end=30),),
            need_text=False,
            need_visual=True,
        )
    report = run(env, **updates)
    blockers = next(s["blockers"] for s in report["stages"] if s["stage"] == "F4")
    expected = {
        "big": "media_size_or_duration_limit",
        "long": "media_size_or_duration_limit",
        "window": "visual_window_outside_declared_duration",
        "estimate_missing": "media_size_duration_estimate_missing",
        "transcription_unapproved": "transcription_not_approved",
    }[problem]
    assert expected in blockers


def test_download_and_process_flags_are_independent(env):
    env.approvals = api.Approvals(
        sources=tuple(
            g.model_copy(update={"download": True, "process": False})
            for g in env.approvals.sources
        )
    )
    report = run(env)
    row = next(
        r for r in report["materials"] if r["material_id"] == env.srt.material_id
    )
    assert row["download_approved"] and not row["process_approved"]
    assert report["blocked"] and "ready_for_processing" not in row["states"]


def test_unrelated_media_failure_does_not_prevent_sufficient_local_reuse(env):
    failed = Unavailability(
        material_id=env.audio.material_id,
        reason="technical_failure",
        decision_reference="synthetic-error",
    )
    report = run(
        env, evidence=(env.transcript,), adequacy=(assess(env),), unavailable=(failed,)
    )
    assert report["selected_strategy"] == "F0" and not report["blocked"]
    row = next(
        r for r in report["materials"] if r["material_id"] == env.srt.material_id
    )
    assert "ready_for_processing" in row["states"]


def test_exhausted_scope_is_blocked_not_success(env):
    excluded = tuple(
        Unavailability(
            material_id=b.material_id,
            reason="missing",
            decision_reference="synthetic-complete-inventory",
        )
        for b in env.bindings
    )
    report = run(env, unavailable=excluded)
    assert report["selected_strategy"] is None and report["blocked"]
    assert report["missing_content"] == ["text"]


def test_remote_references_are_not_available_or_verified_transcripts(env):
    report = run(env)
    assert report["referenced_transcript_languages"] == ["en"]
    assert report["available_transcript_languages"] == []
    assert all(r["remote_availability"] == "not_checked" for r in report["materials"])
    assert all(
        not r["verified"] and "available_remote" not in r["states"]
        for r in report["materials"]
    )


def test_model_state_vocabulary():
    from typing import get_args

    from src.model_materials.media_plan import State

    assert set(get_args(State)) == {
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
    }


@pytest.mark.parametrize(
    "path",
    ["../audio.mp3", "/audio.mp3", "a\\audio.mp3", "a//audio.mp3", "./audio.mp3", ""],
)
def test_media_input_path_contract(path, tmp_path):
    with pytest.raises(ValueError):
        EvidenceRef(
            material_id="synthetic-material",
            kind="media",
            workspace=tmp_path,
            relative_path=path,
        )


def test_local_audio_precedes_local_video_for_text_only(env):
    video_raw = b"synthetic opaque video"
    (env.media_dir / "video.mp4").write_bytes(video_raw)
    env.approvals = api.Approvals(
        sources=tuple(
            grant(env.lecture, video_raw)
            if g.material_id == env.lecture.material_id
            else g
            for g in env.approvals.sources
        )
    )
    references = (
        EvidenceRef(
            material_id=env.lecture.material_id,
            kind="media",
            workspace=env.media_dir,
            relative_path="video.mp4",
        ),
        EvidenceRef(
            material_id=env.audio.material_id,
            kind="media",
            workspace=env.media_dir,
            relative_path="audio.mp3",
        ),
    )
    report = run(env, evidence=references, unavailable=declines(env))
    assert report["selected_strategy"] == "F4"
    assert report["selected_materials"] == [env.audio.material_id]
