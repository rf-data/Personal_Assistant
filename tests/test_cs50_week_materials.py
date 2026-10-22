"""Week discovery and plans use explicit local evidence; never a real acquisition."""

import json
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from scripts.cs50_week import main
from scripts.cs50_workflow_demo import inputs
from src.job_control.models import fingerprint
from src.model_discovery.cs50 import ResourceCandidate
from src.model_materials.materials import MaterialResource
from src.model_materials.week import (
    DiscoverySnapshot,
    LocalSource,
    WeekLimits,
    WeekReport,
    WeekRequest,
    WorkflowReference,
)
from src.tools_materials import batch as api
from src.tools_materials import transcripts
from src.tools_materials.capacity import CapacityLimits
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.processing import MaterialProcessor, make_plan
from src.tools_materials.week import (
    EXPECTED_TASKS,
    plan_week,
    prepare_material_batches,
    prepare_transcript_batches,
    resolve_workflow_reference,
    routing,
)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network in B5 offline tests")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / "snapshots"
    inputs(root)
    week = root / "cs50_python/week0.html"
    extra = """<li>Slides<ul><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.pdf">PDF</a></li><li><a href="https://docs.google.com/presentation/d/example/edit">Google Slides</a></li></ul></li>
<li>Source Code<ul><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/src0/">Index</a></li><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/src0.pdf">PDF</a></li><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/src0.zip">Zip</a></li></ul></li>
<li>Subtitles<ul><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt">SRT</a></li></ul></li>
<li>Transcript<ul><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.txt">TXT</a></li></ul></li>
<li>Audio<ul><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.mp3">MP3</a></li></ul></li>
<li>Shorts<ul><li><a href="/python/shorts/functions/">Functions</a></li></ul></li>
<li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/mystery.xyz">Mystery</a></li>
<li><a href="/python/psets/0/">Problem Set 0</a></li>"""
    week.write_text(
        week.read_text().replace(
            "</ul></li></ul></main>", extra + "</ul></li></ul></main>"
        )
    )
    pset = root / "cs50_python/pset0.html"
    slugs = ("indoor", "playback", "faces", "einstein", "tip")
    pset.write_text(
        "<main><h1>Problem Set 0</h1><ol>"
        + "".join(
            f'<li><a href="{slug}/">{title}</a></li>'
            for slug, title in zip(slugs, EXPECTED_TASKS, strict=True)
        )
        + '<li><a href="indoor/#again">Indoor Voice</a></li></ol></main>'
    )
    manifest = root / "manifest.json"
    data = json.loads(manifest.read_text())
    data["courses"][0]["pages"].append(
        dict(
            file="cs50_python/pset0.html",
            url="https://cs50.harvard.edu/python/psets/0/",
            role="assignment",
            sha256=api.sha(pset.read_bytes()),
        )
    )
    for page in data["courses"][0]["pages"]:
        page["sha256"] = api.sha((root / page["file"]).read_bytes())
    manifest.write_text(json.dumps(data))
    request = WeekRequest(manifest=manifest, source_origin="synthetic")
    return SimpleNamespace(root=root, manifest=manifest, request=request)


def grant(binding, raw=None, **updates):
    refs = {
        key: "synthetic-operator-test-evidence"
        for key in api.SourceApproval.model_fields
        if key.endswith("_reference")
    }
    return api.SourceApproval(
        material_id=binding.material_id,
        source_id=binding.source_id,
        course_id=binding.resource.course_id,
        original_url=binding.original_url,
        process=True,
        download=True,
        expected_sha256=api.sha(raw) if raw else None,
        **refs,
        **updates,
    )


def ready(fixture, rows, tmp_path, mode="process_existing"):
    sources = []
    grants = []
    for index, row in enumerate(rows):
        raw = (
            b'<html><head><title>Fixture</title><meta name="license" content="synthetic"></head><main><p>Read <a href="#x">X</a>.</p><pre>print("hi")\n</pre></main></html>'
            if row.category == "html"
            else b"1\n00:00:01,000 --> 00:00:03,000\nOne\n\n"
        )
        path = tmp_path / f"local-{index}.source"
        path.write_bytes(raw)
        sources.append(
            LocalSource(
                material_id=row.material_id, path=path, expected_sha256=api.sha(raw)
            )
        )
        grants.append(grant(row.binding, raw))
    request = fixture.request.model_copy(
        update=dict(
            mode=mode,
            material_ids=tuple(r.material_id for r in rows),
            local_sources=tuple(sources),
            available_bytes=100 * 1024**3,
            available_memory_mb=768,
            existing_worker_confirmed=True,
        )
    )
    return request, api.Approvals(sources=tuple(grants))


def test_inventory_children_identity_variants_and_no_side_effects(fixture, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No acquisition or parsing during planning")

    monkeypatch.setattr(MaterialDownloader, "obtain", forbidden)
    monkeypatch.setattr(MaterialProcessor, "parse", forbidden)
    before = {p: p.read_bytes() for p in fixture.root.rglob("*") if p.is_file()}
    report = plan_week(fixture.request)
    children = [r for r in report.resources if r.parent_resource_ids]
    assert len(children) == 5 and {r.title for r in children} == set(EXPECTED_TASKS)
    parent = next(r for r in report.resources if r.title == "Problem Set 0")
    assert all(r.parent_resource_ids == (parent.resource_id,) for r in children)
    assert len({r.resource_id for r in children}) == 5
    assert all(
        r.binding.resource.provenance and r.processing_status == "not_requested"
        for r in children
    )
    assert report.counts["processed"] == 0 and not report.scope_processing_complete
    assert all(r.action in {"none", "reference_only"} for r in report.resources)
    assert WeekReport.model_validate_json(report.model_dump_json()) == report
    assert plan_week(fixture.request) == report
    assert {p: p.read_bytes() for p in before} == before
    original = make_plan(fixture.manifest)
    assert {
        b.material_id for b in original.materials if "0" in b.resource.section_keys
    }.issubset({r.material_id for r in report.resources})


@pytest.mark.parametrize(
    "role,fmt,url,category,adapter",
    [
        (
            "notes",
            "html",
            "https://cs50.harvard.edu/python/notes/0/",
            "html",
            "c18_material",
        ),
        (
            "source_code",
            "pdf",
            "https://cdn.cs50.net/python/2022/x/lectures/0/src0.pdf",
            "pdf",
            "c18_material",
        ),
        (
            "slides",
            "pdf",
            "https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.pdf",
            "pdf",
            "c18_material",
        ),
        (
            "audio",
            "mp3",
            "https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.mp3",
            "media",
            "media_plan_only",
        ),
        (
            "short",
            "html",
            "https://cs50.harvard.edu/python/shorts/functions/",
            "media",
            "media_plan_only",
        ),
        (
            "slides",
            "unknown",
            "https://docs.google.com/presentation/d/example/edit",
            "presentation",
            "presentation_export",
        ),
        (
            "other",
            "xyz",
            "https://cdn.cs50.net/python/mystery.xyz",
            "unknown",
            "unsupported",
        ),
        (
            "subtitles",
            "srt",
            "https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt",
            "transcript",
            "offline_transcript",
        ),
        (
            "transcript",
            "txt",
            "https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.txt",
            "transcript",
            "offline_transcript",
        ),
    ],
)
def test_routing(role, fmt, url, category, adapter):
    r = ResourceCandidate(
        course_id="cs50_python",
        role=role,
        original_url=url,
        section_keys=("0",),
        language="en" if role in {"subtitles", "transcript"} else None,
    )
    binding = MaterialResource(
        resource=r,
        lecture_ids=("resource:lecture",),
        original_url=url,
        format=fmt,
        role=role,
        language=r.language,
    )
    actual = routing(binding, WeekLimits())
    assert actual[0] == category and actual[2] == adapter
    if category == "pdf":
        assert actual[3].max_bytes == 1048576 and actual[3].max_pages == 20


@pytest.mark.parametrize(
    "role,fmt,path",
    [
        ("source_code", "html", "src0/"),
        ("notes", "html", "src0/"),
        ("notes", "html", "src0/index.html"),
        ("notes", "html", "hello.py"),
        ("notes", "html", "src0.zip"),
        ("subtitles", "srt", "hello.py"),
        ("notes", "html", "hello%2epy"),
        ("notes", "html", "hello%252epy"),
        ("notes", "html", "source.tar.gz"),
    ],
)
def test_code_cannot_be_reclassified_as_documents(role, fmt, path):
    url = "https://cdn.cs50.net/python/2022/x/lectures/0/" + path
    r = ResourceCandidate(
        course_id="cs50_python", role=role, original_url=url, section_keys=("0",)
    )
    b = MaterialResource(resource=r, original_url=url, format=fmt, role=role)
    assert routing(b, WeekLimits())[:3] == ("code", "manual_only", "manual_code")


def test_manual_resources_do_not_reach_batches_even_with_grants(
    fixture, tmp_path, monkeypatch
):
    rows = [
        r
        for r in plan_week(fixture.request).resources
        if r.acquisition_policy == "manual_only"
    ]
    request, approvals = ready(fixture, rows, tmp_path)
    original = api.plan

    def guarded(manifest, courses, resources=(), **kwargs):
        assert not set(resources) & {r.material_id for r in rows}
        return original(manifest, courses, resources, **kwargs)

    monkeypatch.setattr(api, "plan", guarded)
    report, batches = prepare_material_batches(request, approvals)
    assert not batches
    assert all(
        r.action == "reference_only" and r.processing_status == "not_requested"
        for r in report.resources
        if r.selected
    )
    assert all(
        not r.blockers and not r.missing_approvals
        for r in report.resources
        if r.selected
    )
    assert not report.scope_processing_complete


def test_existing_document_inputs_use_existing_batches(fixture, tmp_path):
    row = next(
        r for r in plan_week(fixture.request).resources if r.binding.role == "notes"
    )
    request, approvals = ready(fixture, [row], tmp_path)
    report, batches = prepare_material_batches(request, approvals)
    assert len(batches) == 1 and batches[0].materials == (row.binding,)
    assert (
        next(r for r in report.resources if r.selected).action == "ready_c18_submission"
    )
    assert not report.execution_supported and not report.scope_processing_complete
    assert not (tmp_path / "archive").exists()


def test_discovered_children_have_explicit_c18_adapter_blocker(fixture, tmp_path):
    row = next(r for r in plan_week(fixture.request).resources if r.title == "Einstein")
    request, approvals = ready(fixture, [row], tmp_path)
    report, batches = prepare_material_batches(request, approvals)
    assert not batches
    assert (
        "assignment_child_c18_adapter_not_integrated"
        in next(r for r in report.resources if r.selected).blockers
    )


@pytest.mark.parametrize(
    "change,blocker",
    [
        ("approval", "source_process_approval"),
        ("hash", "local_source_not_pinned_to_current_source_approval"),
        ("missing", "local_source_missing_unsafe_changed_or_over_limit"),
        ("size", "local_source_missing_unsafe_changed_or_over_limit"),
        ("capacity", "capacity_unknown_or_insufficient_including_5gib_reserve"),
        ("memory", "memory_capacity_unknown_or_insufficient"),
        ("worker", "existing_single_worker_and_queue_limits_not_confirmed"),
    ],
)
def test_missing_approval_and_resource_limits(fixture, tmp_path, change, blocker):
    row = next(
        r for r in plan_week(fixture.request).resources if r.binding.role == "notes"
    )
    request, approvals = ready(fixture, [row], tmp_path)
    if change == "approval":
        approvals = api.Approvals()
    elif change == "hash":
        request = request.model_copy(
            update={
                "local_sources": (
                    request.local_sources[0].model_copy(
                        update={"expected_sha256": None}
                    ),
                )
            }
        )
    elif change == "missing":
        request.local_sources[0].path.unlink()
    elif change == "size":
        request.local_sources[0].path.write_bytes(b"x" * (1048576 + 1))
    else:
        request = request.model_copy(
            update={"available_bytes": None}
            if change == "capacity"
            else {"available_memory_mb": None}
            if change == "memory"
            else {"existing_worker_confirmed": False}
        )
    report, batches = prepare_material_batches(request, approvals)
    actual = next(r for r in report.resources if r.selected)
    assert blocker in (*actual.blockers, *actual.missing_approvals) and not batches


@pytest.mark.parametrize("mode", ["plan", "approved_acquisition"])
def test_modes_never_acquire(fixture, mode, monkeypatch):
    monkeypatch.setattr(
        MaterialDownloader,
        "obtain",
        lambda *a, **k: pytest.fail("acquisition forbidden"),
    )
    report = plan_week(fixture.request.model_copy(update={"mode": mode}))
    assert report.counts["ready"] == 0 and not report.execution_supported
    assert any(
        r.blockers or r.missing_approvals for r in report.resources if r.selected
    )


def test_scope_count_and_total_size_limits(fixture, tmp_path):
    report = plan_week(fixture.request.model_copy(update={"mode": "plan"}))
    assert any(
        "selected_scope_exceeds_material_limit" in r.blockers
        for r in report.resources
        if r.selected
    )
    row = next(r for r in report.resources if r.binding.role == "notes")
    request, approvals = ready(fixture, [row], tmp_path)
    request = request.model_copy(update={"limits": WeekLimits(total_raw_bytes=1)})
    report, batches = prepare_material_batches(request, approvals)
    assert not batches
    assert (
        "total_raw_byte_limit"
        in next(r for r in report.resources if r.selected).blockers
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_bytes": 1048577},
        {"max_materials": 9},
        {"max_parallel": 2},
        {"max_queued": 2},
        {"reserve_bytes": 1},
    ],
)
def test_limits_cannot_be_raised_or_reserve_weakened(kwargs):
    with pytest.raises(ValidationError):
        WeekLimits(**kwargs)


def test_controller_root_named_jobs_is_not_doubled(tmp_path):
    root = tmp_path / "jobs"
    job = "job_" + "a" * 32
    name = f"jobs/{job}/results/stages/source/normalized.v1.json"
    path = root / name
    path.parent.mkdir(parents=True)
    path.write_bytes(b"{}")
    ref = WorkflowReference(
        material_id="material:x",
        controller_root=root,
        job_id=job,
        relative_path=name,
        sha256=api.sha(b"{}"),
    )
    assert resolve_workflow_reference(ref) == path
    with pytest.raises(ValueError):
        resolve_workflow_reference(ref.model_copy(update={"sha256": "0" * 64}))
    with pytest.raises(ValidationError):
        WorkflowReference(
            material_id="x",
            controller_root=root,
            job_id=job,
            relative_path="../escape",
            sha256="0" * 64,
        )


def test_supplemental_discovery_export_is_explicit_hash_bound(fixture, tmp_path):
    pset = fixture.root / "cs50_python/pset0.html"
    source = tmp_path / "operator-export.html"
    source.write_bytes(pset.read_bytes())
    data = json.loads(fixture.manifest.read_text())
    data["courses"][0]["pages"] = [
        p for p in data["courses"][0]["pages"] if p["role"] != "assignment"
    ]
    fixture.manifest.write_text(json.dumps(data))
    supplied = DiscoverySnapshot(
        label="operator/problem-set-0.html",
        path=source,
        original_url="https://cs50.harvard.edu/python/psets/0/",
        sha256=api.sha(source.read_bytes()),
    )
    assert not any(r.parent_resource_ids for r in plan_week(fixture.request).resources)
    request = fixture.request.model_copy(update={"discovery_exports": (supplied,)})
    before = source.read_bytes()
    assert len([r for r in plan_week(request).resources if r.parent_resource_ids]) == 5
    assert source.read_bytes() == before
    source.write_bytes(before + b"changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        plan_week(request)


def test_cli_is_read_only_and_reports_scope(fixture, capsys):
    before = {p: p.read_bytes() for p in fixture.root.rglob("*") if p.is_file()}
    assert main(["--manifest", str(fixture.manifest)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["counts"]["processed"] == 0 and not output["subject_matter_verified"]
    assert {p: p.read_bytes() for p in before} == before


def completed_materials(fixture, tmp_path, roles=("notes",)):
    from src.model_materials.materials import MaterialPlan
    from src.model_materials.media_plan import EvidenceRef

    rows = [
        r
        for r in plan_week(fixture.request).resources
        if r.binding.role in roles
        and not r.parent_resource_ids
        and r.category == "html"
    ]
    request, approvals = ready(fixture, rows, tmp_path)
    root = tmp_path / "material-archive"
    root.mkdir(mode=0o700)
    graph = make_plan(fixture.manifest)
    bindings = tuple(api.reviewed(r.binding) for r in rows)
    plan = MaterialPlan(courses=graph.courses, materials=bindings)
    plan_file = tmp_path / "material-plan.json"
    plan_file.write_text(plan.model_dump_json())
    refs = []
    for row, local, binding in zip(rows, request.local_sources, bindings, strict=True):
        downloader = MaterialDownloader(root, max_bytes=1048576)
        downloader.obtain(binding, execute=True, local_file=local.path)
        MaterialProcessor(root).parse(binding, execute=True, config=row.parser)
        _, receipt = downloader.paths(binding)
        refs.append(
            EvidenceRef(
                material_id=row.material_id,
                kind="material",
                workspace=root,
                receipt_sha256=api.sha(receipt.read_bytes()),
                plan=plan_file,
            )
        )
    return (
        request.model_copy(
            update={
                "local_sources": (),
                "evidence": tuple(refs),
                "available_bytes": None,
                "available_memory_mb": None,
                "existing_worker_confirmed": False,
            }
        ),
        approvals,
        root,
    )


def test_existing_verified_materials_are_reused_without_processing(
    fixture, tmp_path, monkeypatch
):
    request, approvals, root = completed_materials(fixture, tmp_path)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    monkeypatch.setattr(
        MaterialProcessor,
        "parse",
        lambda *a, **k: pytest.fail("Never reprocess verified output"),
    )
    first, batches = prepare_material_batches(request, approvals)
    assert not batches and first.counts["reused"] == 1
    assert first.scope_processing_complete and first.technical_workflow_complete
    assert not first.full_week_discovery_verified and not first.subject_matter_verified
    assert first == plan_week(request, approvals)
    assert next(r for r in first.resources if r.selected).planned_steps == (
        "verify_existing_result",
        "reuse_without_processing",
    )
    assert {p: p.read_bytes() for p in before} == before
    # A parser/config change retains the old artifacts and blocks automatic reuse.
    changed = plan_week(
        request.model_copy(update={"limits": WeekLimits(max_bytes=524288)}), approvals
    )
    assert changed.counts["reused"] == 0 and not changed.scope_processing_complete
    assert {p: p.read_bytes() for p in before} == before


def test_one_corrupt_material_does_not_damage_another(fixture, tmp_path):
    request, approvals, root = completed_materials(
        fixture, tmp_path, roles=("notes", "problem_set")
    )
    first = plan_week(request, approvals)
    assert first.counts["reused"] == 2
    binding = next(
        r.binding
        for r in first.resources
        if r.binding.role == "problem_set" and r.selected
    )
    raw, _ = MaterialDownloader(root).paths(binding)
    raw.write_bytes(b"changed")
    report = plan_week(request, approvals)
    assert report.counts["reused"] == 1 and not report.scope_processing_complete
    assert (
        next(
            r for r in report.resources if r.selected and r.binding.role == "notes"
        ).processing_status
        == "completed"
    )
    assert (
        next(
            r
            for r in report.resources
            if r.selected and r.binding.role == "problem_set"
        ).quality_status
        == "failed"
    )


@pytest.mark.parametrize("fmt", ["srt", "txt"])
def test_existing_transcript_adapter_and_timestamp_preservation(
    fixture, tmp_path, monkeypatch, fmt
):
    from src.model_materials.media_plan import EvidenceRef

    monkeypatch.setattr(
        "shutil.disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3)
    )
    row = next(
        r for r in plan_week(fixture.request).resources if r.binding.format == fmt
    )
    request, approvals = ready(fixture, [row], tmp_path)
    report, batches = prepare_transcript_batches(request, approvals)
    assert len(batches) == 1
    raw = (
        b"1\n00:00:01,000 --> 00:00:03,000\nOne\n\n"
        if fmt == "srt"
        else b"Plain text has no timestamps.\n"
    )
    source = request.local_sources[0].path
    source.write_bytes(raw)
    approvals = api.Approvals(sources=(grant(row.binding, raw),))
    batch = batches[0]
    root = tmp_path / "transcript-archive"
    result = transcripts.run(
        batch,
        root,
        approvals,
        {row.binding.source_id: source},
        action="import",
        limits=CapacityLimits(
            reserve_bytes=5 * 1024**3, archive_bytes=64 * 1048576, max_materials=1
        ),
    )
    assert result["materials"][0]["status"] == "processed"
    batch_file = tmp_path / "transcript-batch.json"
    batch_file.write_text(
        json.dumps(
            {
                "batch": batch.model_dump(mode="json"),
                "sha256": fingerprint(batch.model_dump(mode="json")),
            }
        )
    )
    folder = root / row.material_id.split(":")[-1]
    ref = EvidenceRef(
        material_id=row.material_id,
        kind="transcript",
        workspace=root,
        batch=batch_file,
        receipt_sha256=api.sha((folder / "receipt.json").read_bytes()),
    )
    observed = request.model_copy(update={"local_sources": (), "evidence": (ref,)})
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    reused = plan_week(observed, approvals)
    assert reused.counts["reused"] == 1 and reused.scope_processing_complete
    payload = json.loads((folder / "transcript.json").read_bytes())
    assert payload["segments"][0]["start"] == (1.0 if fmt == "srt" else None)
    assert payload["segments"][0]["end"] == (3.0 if fmt == "srt" else None)
    assert {p: p.read_bytes() for p in before} == before


def test_report_rejects_inconsistent_counts_and_completion(fixture):
    report = plan_week(fixture.request)
    payload = json.loads(report.model_dump_json())
    payload["counts"]["processed"] = 99
    with pytest.raises(ValidationError):
        WeekReport.model_validate_json(json.dumps(payload))
    payload = json.loads(report.model_dump_json())
    payload["scope_processing_complete"] = True
    with pytest.raises(ValidationError):
        WeekReport.model_validate_json(json.dumps(payload))


def test_real_operator_exports_read_only():
    import os

    from src.model_materials.materials import NormalizedDocument

    export = os.environ.get("CS50_WEEK0_QUALITY_EXPORT")
    if not export:
        pytest.skip("Explicit local real-pilot export root not supplied")
    root = Path(export)
    originals = []
    before = {}
    for folder, url, label, blocks, codes in [
        ("material_01", "https://cs50.harvard.edu/python/notes/0/", "notes0", 237, 34),
        ("material_02", "https://cs50.harvard.edu/python/psets/0/", "pset0", 28, 0),
    ]:
        directory = root / folder
        for filename in ["original.html", "normalized.v1.json", "quality.v1.json"]:
            before[directory / filename] = (directory / filename).read_bytes()
        raw = before[directory / "original.html"]
        doc = NormalizedDocument.model_validate_json(
            before[directory / "normalized.v1.json"]
        )
        assert (
            len(doc.blocks) == blocks
            and sum(b.type == "code" for b in doc.blocks) == codes
        )
        assert doc.raw_sha256 == api.sha(raw)
        originals.append(
            DiscoverySnapshot(
                label=f"operator_export/{label}.html",
                role="lecture_notes" if folder == "material_01" else "assignment",
                path=directory / "original.html",
                original_url=url,
                sha256=api.sha(raw),
            )
        )
    request = WeekRequest(
        manifest=Path("docs/course_sources/cs50/manifest.json").absolute(),
        discovery_exports=tuple(originals),
    )
    report = plan_week(request)
    assert report.counts["resources"] == 21 and report.counts["material_variants"] == 28
    assert report.counts["manual_only"] == 2 and report.counts["processed"] == 0
    assert all(
        r.acquisition_status == "local_present"
        for r in report.resources
        if r.category == "html" and r.local_snapshots
    )
    tasks = [
        r
        for r in report.resources
        if r.parent_resource_ids and r.binding.role == "problem_set"
    ]
    assert len(tasks) == 5 and {r.title for r in tasks} == set(EXPECTED_TASKS)
    assert all(r.binding.resource.provenance for r in tasks)
    assert not any(g.startswith("task_not_proven:") for g in report.gaps)
    assert not report.scope_processing_complete
    assert {p: p.read_bytes() for p in before} == before


@pytest.mark.parametrize("role", ["slides", "source_code"])
def test_pdf_v2_adapter_preserves_raw_and_page_provenance(fixture, tmp_path, role):
    from src.model_materials.materials import NormalizedDocument

    row = next(
        r
        for r in plan_week(fixture.request).resources
        if r.binding.role == role and r.category == "pdf"
    )
    raw = Path("tests/fixtures/material_quality/source.pdf").read_bytes()
    source = tmp_path / "synthetic.pdf"
    source.write_bytes(raw)
    request = fixture.request.model_copy(
        update={
            "mode": "process_existing",
            "material_ids": (row.material_id,),
            "local_sources": (
                LocalSource(
                    material_id=row.material_id,
                    path=source,
                    expected_sha256=api.sha(raw),
                ),
            ),
            "available_bytes": 100 * 1024**3,
            "available_memory_mb": 768,
            "existing_worker_confirmed": True,
        }
    )
    approvals = api.Approvals(sources=(grant(row.binding, raw),))
    report, batches = prepare_material_batches(request, approvals)
    assert len(batches) == 1
    root = tmp_path / "pdf-archive"
    binding = api.reviewed(row.binding)
    downloader = MaterialDownloader(root, max_bytes=1048576)
    downloader.obtain(binding, execute=True, local_file=source)
    receipt = MaterialProcessor(root).parse(binding, execute=True, config=row.parser)
    doc = NormalizedDocument.model_validate_json(
        (root / receipt.normalized_path).read_bytes()
    )
    assert receipt.raw_sha256 == api.sha(raw) and source.read_bytes() == raw
    assert doc.parser.max_pages == 20 and doc.parser.max_bytes == 1048576
    assert all(
        b.location.page is not None and b.location.bbox is not None for b in doc.blocks
    )
    assert doc.binding.lecture_ids == row.binding.lecture_ids
    assert doc.blocks and doc.raw_sha256 == api.sha(raw)


def test_discovery_does_not_extend_or_parse_code_indexes(fixture, monkeypatch):
    from src.tools_materials import code_discovery

    monkeypatch.setattr(
        code_discovery,
        "extend",
        lambda *a, **kw: pytest.fail("Do not traverse code indexes"),
    )
    report = plan_week(fixture.request)
    assert any(
        r.acquisition_policy == "manual_only" and r.title == "Index"
        for r in report.resources
    )


def test_wrong_source_export_and_symlink_input_are_blocked(fixture, tmp_path):
    row = next(
        r for r in plan_week(fixture.request).resources if r.binding.role == "notes"
    )
    request, approvals = ready(fixture, [row], tmp_path)
    link = tmp_path / "linked-source"
    link.symlink_to(request.local_sources[0].path)
    unsafe = request.model_copy(
        update={
            "local_sources": (
                request.local_sources[0].model_copy(update={"path": link}),
            )
        }
    )
    report, batches = prepare_material_batches(unsafe, approvals)
    assert (
        not batches
        and next(r for r in report.resources if r.selected).action == "blocked"
    )
    supplied = DiscoverySnapshot(
        label="foreign.html",
        path=request.local_sources[0].path,
        original_url="https://example.org/foreign/",
        sha256="0" * 64,
    )
    with pytest.raises(ValueError, match="outside"):
        plan_week(fixture.request.model_copy(update={"discovery_exports": (supplied,)}))


def test_capacity_uses_existing_guardian_envelope(fixture, tmp_path):
    from src.job_control.registry import WORKFLOW_PROCESS

    limits = WeekLimits()
    assert limits.memory_mb * 1048576 == WORKFLOW_PROCESS.memory_bytes
    assert limits.wall_seconds == WORKFLOW_PROCESS.timeout_seconds
    assert limits.cpu_seconds == WORKFLOW_PROCESS.cpu_seconds
    row = next(
        r for r in plan_week(fixture.request).resources if r.binding.role == "notes"
    )
    request, approvals = ready(fixture, [row], tmp_path)
    insufficient = request.model_copy(update={"available_memory_mb": 512})
    report, batches = prepare_material_batches(insufficient, approvals)
    assert not batches
    assert (
        "memory_capacity_unknown_or_insufficient"
        in next(r for r in report.resources if r.selected).blockers
    )
