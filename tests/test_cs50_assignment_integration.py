"""Pinned overview discovery through the existing B5 -> C18 -> C16 path."""

import json
import os
import socket
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from scripts.job_control_demo import DEMO_TOKEN
from src.job_control.catalog import prepare_indexes
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.models import (
    TERMINAL,
    CatalogEntry,
    Identity,
    Settings,
    fingerprint,
)
from src.model_materials.week import DiscoverySnapshot, LocalSource, WeekRequest
from src.tools_materials import batch as api
from src.tools_materials.assignments import for_week
from src.tools_materials.capacity import CapacityLimits
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.processing import make_plan
from src.tools_materials.week import plan_week, prepare_material_batches
from src.workflows.definition import prepare
from src.workflows.models import Definition
from src.workflows.service import submit
from tests.test_cs50_week_materials import fixture as fixture
from tests.test_cs50_week_materials import grant


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network in assignment integration tests")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def selected_children(report):
    return [r for r in report.resources if r.parent_resource_ids]


def bundle(batch, root, raw):
    """A reconstruction-only bundle; empty raw means no task contents supplied."""
    root.mkdir(mode=0o700)
    for name in batch.files:
        target = root / "discovery" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(batch.input_path(name).read_bytes())
    definition = Definition(
        schema_version=batch.schema_version,
        course_id="cs50_python",
        sources={batch.materials[0].source_id: "raw.source"},
        assignment_snapshots=tuple(
            s.model_copy(update=dict(path=Path("discovery") / s.file))
            for s in batch.assignment_snapshots
        ),
    )
    (root / "workflow.json").write_text(definition.model_dump_json())
    (root / "raw.source").write_bytes(raw)
    return CatalogEntry(
        kind="workflow_bundle",
        root=root,
        files={
            p.relative_to(root).as_posix(): api.sha(p.read_bytes())
            for p in root.rglob("*")
            if p.is_file()
        },
        roles=dict(
            manifest="discovery/" + batch.manifest.name, workflow="workflow.json"
        ),
        course_ids=("cs50_python",),
    )


def test_real_export_five_ids_provenance_and_worker_admission(tmp_path):
    export = os.environ.get("CS50_WEEK0_QUALITY_EXPORT")
    if not export:
        pytest.skip("Explicit operator original required")
    root = Path(export)
    before = {
        root / f / n: (root / f / n).read_bytes()
        for f in ("material_01", "material_02")
        for n in ("original.html", "normalized.v1.json", "quality.v1.json")
    }
    source = root / "material_02/original.html"
    request = WeekRequest(
        manifest=Path("docs/course_sources/cs50/manifest.json").absolute(),
        discovery_exports=(
            DiscoverySnapshot(
                label="operator_export/material_02.html",
                path=source,
                original_url="https://cs50.harvard.edu/python/psets/0/",
                sha256=api.sha(before[source]),
            ),
        ),
    )
    legacy = selected_children(plan_week(request))
    upgraded = request.model_copy(update=dict(assignment_discovery=True))
    children = selected_children(plan_week(upgraded))
    assert len(children) == 5
    assert [r.binding for r in children] == [r.binding for r in legacy]
    assert [r.parent_resource_ids for r in children] == [
        r.parent_resource_ids for r in legacy
    ]
    baseline = json.loads(
        Path("docs/deployment/c26a/week0_resources.v1.json").read_bytes()
    )
    assert {r.resource_id for r in children} == {
        r["resource_id"] for r in baseline["resources"] if r["parent_resource_ids"]
    }
    assert all(
        "assignment_child_not_in_existing_c18_discovery_graph" not in r.limitations
        for r in children
    )
    for index, child in enumerate(children):
        batch = api.plan(
            request.manifest,
            ["cs50_python"],
            [child.material_id],
            assignment_snapshots=for_week(upgraded),
        )
        assert batch.schema_version == 2
        entry = bundle(batch, tmp_path / f"bundle-{index}", b"")
        prepared = prepare(entry)
        assert prepared.definition.schema_version == 2
        assert prepared.bindings[child.material_id].resource == child.binding.resource
        assert len(prepared.stages) == 5
        assert any(
            s.endswith("operator_export/material_02.html")
            for s in prepared.planning_hashes
        )
        settings = Settings(root=tmp_path / f"jobs-{index}", catalog={"child": entry})
        indexed = prepare_indexes(settings)["child"]
        assert prepare(entry, plan=indexed) == prepared
    assert {p: p.read_bytes() for p in before} == before
    # This test deliberately does NOT process the unavailable actual task contents.


def test_opt_in_preserves_legacy_bytes_and_requires_overview(fixture):
    request = fixture.request
    legacy = plan_week(request)
    child = selected_children(legacy)[0]
    assert "assignment_child_not_in_existing_c18_discovery_graph" in child.limitations
    assert "assignment_discovery" not in request.model_dump()
    old = Definition(course_id="cs50_python", sources={"resource:test": "raw.source"})
    assert old.schema_version == 1 and "assignment_snapshots" not in old.model_dump()
    assert Definition.model_validate_json(old.model_dump_json()) == old
    notes = next(r for r in legacy.resources if r.binding.role == "notes")
    batch = api.plan(
        fixture.manifest, ["cs50_python"], [notes.material_id], synthetic=True
    )
    assert (
        batch.schema_version == 1 and "assignment_snapshots" not in batch.model_dump()
    )
    assert api.Batch.model_validate_json(batch.model_dump_json()) == batch
    with pytest.raises(ValidationError):
        Definition(
            course_id="cs50_python", schema_version=2, sources={"resource:test": "raw"}
        )


@pytest.mark.parametrize(
    "problem", ["hash", "duplicate", "symlink", "foreign_url", "label_collision"]
)
def test_changed_or_ambiguous_overview_rejected(fixture, tmp_path, problem):
    request = fixture.request.model_copy(update=dict(assignment_discovery=True))
    refs = list(for_week(request))
    ref = refs[0]
    if problem == "hash":
        refs = [ref.model_copy(update=dict(sha256="0" * 64))]
    elif problem == "duplicate":
        refs = refs + refs
    elif problem == "symlink":
        path = tmp_path / "link.html"
        path.symlink_to(ref.path)
        refs = [ref.model_copy(update=dict(path=path))]
    elif problem == "foreign_url":
        refs = [
            ref.model_copy(update=dict(url="https://cs50.harvard.edu/sql/psets/0/"))
        ]
    elif problem == "label_collision":
        refs = [ref.model_copy(update=dict(file="cs50_python/week0.html"))]
    with pytest.raises((ValueError, TypeError)):
        make_plan(fixture.manifest, assignment_snapshots=refs)


def test_cached_legacy_plan_and_incomplete_catalog_cannot_bypass_reconstruction(
    fixture, tmp_path
):
    request = fixture.request.model_copy(update=dict(assignment_discovery=True))
    child = selected_children(plan_week(request))[0]
    batch = api.plan(
        fixture.manifest,
        ["cs50_python"],
        [child.material_id],
        synthetic=True,
        assignment_snapshots=for_week(request),
    )
    entry = bundle(batch, tmp_path / "bundle", b"")
    with pytest.raises(ValueError, match="Cached discovery"):
        prepare(entry, plan=make_plan(entry.root / entry.roles["manifest"]))
    workflow = json.loads((entry.root / "workflow.json").read_bytes())
    workflow["assignment_snapshots"][0]["path"] = "../outside.html"
    with pytest.raises(ValidationError):
        Definition.model_validate(workflow)
    name = next(
        s.path.as_posix() for s in prepare(entry).definition.assignment_snapshots
    )
    entry_missing = entry.model_copy(
        update=dict(files={k: v for k, v in entry.files.items() if k != name})
    )
    with pytest.raises(ValueError):
        prepare(entry_missing)
    snapshot = entry.root / name
    snapshot.write_bytes(b"<main>changed</main>")
    with pytest.raises(ValueError):
        prepare(entry)


def test_batch_hash_material_and_snapshot_closure_roundtrip(fixture, tmp_path):
    request = fixture.request.model_copy(update=dict(assignment_discovery=True))
    child = selected_children(plan_week(request))[0]
    batch = api.plan(
        fixture.manifest,
        ["cs50_python"],
        [child.material_id],
        synthetic=True,
        assignment_snapshots=for_week(request),
    )
    path = tmp_path / "batch.json"
    payload = dict(
        batch=batch.model_dump(mode="json"),
        sha256=fingerprint(batch.model_dump(mode="json")),
    )
    path.write_text(json.dumps(payload))
    assert api.load_batch(path) == batch
    snapshot = batch.assignment_snapshots[0]
    snapshot.path.write_bytes(
        snapshot.path.read_bytes().replace(b"indoor/", b"changed/")
    )
    with pytest.raises(ValueError):
        api.load_batch(path)


def test_synthetic_child_seal_and_real_c16_worker(fixture, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "shutil.disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3)
    )
    base = fixture.request.model_copy(update=dict(assignment_discovery=True))
    children = selected_children(plan_week(base))
    inputs = []
    grants = []
    raw = b'<html><head><title>Synthetic task</title></head><main><h1>Synthetic fixture</h1><p>Only offline test content.</p><pre>print("fixture")\n</pre></main></html>'
    for index, child in enumerate(children):
        path = tmp_path / f"synthetic-{index}.html"
        path.write_bytes(raw)
        path.chmod(0o600)
        inputs.append(
            LocalSource(
                material_id=child.material_id, path=path, expected_sha256=api.sha(raw)
            )
        )
        grants.append(grant(child.binding, raw))
    request = base.model_copy(
        update=dict(
            mode="process_existing",
            material_ids=tuple(r.material_id for r in children),
            local_sources=tuple(inputs),
            available_bytes=100 * 1024**3,
            available_memory_mb=768,
            existing_worker_confirmed=True,
        )
    )
    approvals = api.Approvals(sources=tuple(grants))
    report, batches = prepare_material_batches(request, approvals)
    assert len(batches) == 5 and all(
        r.action == "ready_c18_submission" for r in report.resources if r.selected
    )
    archive = tmp_path / "archive"
    archive.mkdir(mode=0o700)
    entries = {}
    limits = CapacityLimits(reserve_bytes=5 * 1024**3, max_materials=1)
    for index, batch in enumerate(batches):
        binding = batch.materials[0]
        MaterialDownloader(archive).obtain(
            api.reviewed(binding), execute=True, local_file=inputs[index].path
        )
        result = api.seal(
            batch, archive, tmp_path / f"catalog-{index}", approvals, limits=limits
        )
        assert result["materials"][0]["status"] == "sealed", result
        entry = CatalogEntry.model_validate(next(iter(result["catalog"].values())))
        assert (
            prepare(entry).bindings[binding.material_id].source_id == binding.source_id
        )
        entries[f"child_{index}"] = entry
    settings = Settings(
        root=tmp_path / "jobs",
        catalog=entries,
        execution_enabled=True,
        workflows_enabled=True,
        max_queued=1,
        max_parallel=1,
        identities=(
            Identity(
                subject="synthetic",
                role="operator",
                courses=("cs50_python",),
                token_sha256=api.sha(DEMO_TOKEN.encode()),
            ),
        ),
    )
    actor = settings.identities[0]
    executor = Executor(settings)
    try:
        controller = Controller(settings)
        job = submit(settings, actor, "child_0", "synthetic_child")
        until = time.monotonic() + 30
        while controller.get(actor, job.job_id).status not in TERMINAL:
            assert time.monotonic() < until
            executor.step()
            time.sleep(0.02)
        assert controller.get(actor, job.job_id).status == "completed"
    finally:
        executor.close()


def test_opt_in_does_not_grant_missing_source_approval(fixture, tmp_path):
    request = fixture.request.model_copy(update=dict(assignment_discovery=True))
    children = selected_children(plan_week(request))
    selected = request.model_copy(
        update=dict(
            mode="process_existing",
            material_ids=(children[0].material_id,),
            available_bytes=100 * 1024**3,
            available_memory_mb=768,
            existing_worker_confirmed=True,
        )
    )
    report, batches = prepare_material_batches(selected, api.Approvals())
    row = next(r for r in report.resources if r.selected)
    assert row.missing_approvals and row.action == "blocked" and not batches
    assert "assignment_child_c18_adapter_not_integrated" not in row.blockers


def test_version_two_cli_and_b6_keep_explicit_opt_in(fixture, tmp_path, monkeypatch):
    from scripts.cs50_batch import main
    from src.model_materials.course import CourseRequest
    from src.model_materials.week import ProfiledWeekRequest
    from src.tools_materials.course import plan_course
    from src.tools_materials.profiles import load_profile

    monkeypatch.setattr(
        "shutil.disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3)
    )
    base = fixture.request.model_copy(update=dict(assignment_discovery=True))
    child = selected_children(plan_week(base))[0]
    refs = for_week(base)
    file = tmp_path / "assignment-inputs.json"
    file.write_text(json.dumps([s.model_dump(mode="json") for s in refs]))
    out = tmp_path / "batch.json"
    assert (
        main(
            [
                "plan",
                "--manifest",
                str(fixture.manifest),
                "--course",
                "cs50_python",
                "--resource",
                child.material_id,
                "--synthetic",
                "--assignment-snapshots",
                str(file),
                "--output",
                str(out),
            ]
        )
        == 0
    )
    batch = api.load_batch(out)
    assert (
        batch.schema_version == 2 and batch.materials[0].source_id == child.resource_id
    )
    profile = load_profile(fixture.manifest, "cs50_python")
    week = ProfiledWeekRequest(
        **{**base.model_dump(), "schema_version": 2, "profile": profile}
    )
    course = CourseRequest(
        manifest=fixture.manifest,
        profile=profile,
        course_id="cs50_python",
        weeks=("0",),
        source_origin="synthetic",
        mode="plan",
        week_inputs=(week,),
    )
    report = plan_course(course)
    assert report.weeks[0].report
    assert all(
        "assignment_child_not_in_existing_c18_discovery_graph" not in r.limitations
        for r in selected_children(report.weeks[0].report)
    )
    assert report.preflight.production_decision == "blocked"
    assert not report.preflight.execution_supported


def test_overview_cannot_bypass_manual_code_policy(fixture, tmp_path):
    request = fixture.request.model_copy(update=dict(assignment_discovery=True))
    overview = for_week(request)[0]
    overview.path.write_bytes(
        overview.path.read_bytes().replace(
            b"</main>", b'<a href="attack.py/">Code disguised as task</a></main>'
        )
    )
    data = json.loads(fixture.manifest.read_bytes())
    for page in data["courses"][0]["pages"]:
        if page["file"] == overview.file:
            page["sha256"] = api.sha(overview.path.read_bytes())
    fixture.manifest.write_text(json.dumps(data))
    refs = for_week(request)
    unsafe = next(
        b
        for b in make_plan(fixture.manifest, assignment_snapshots=refs).materials
        if b.original_url.endswith("/attack.py/")
    )
    with pytest.raises(PermissionError, match="manual"):
        api.plan(
            fixture.manifest,
            ["cs50_python"],
            [unsafe.material_id],
            assignment_snapshots=refs,
        )
    # A hand-authored v2 bundle must be rejected at the worker boundary as well.
    normal = selected_children(plan_week(request))[0]
    batch = api.plan(
        fixture.manifest,
        ["cs50_python"],
        [normal.material_id],
        assignment_snapshots=refs,
    )
    entry = bundle(batch, tmp_path / "manual-policy", b"")
    value = json.loads((entry.root / "workflow.json").read_bytes())
    value["sources"] = {unsafe.source_id: "raw.source"}
    content = json.dumps(value).encode()
    (entry.root / "workflow.json").write_bytes(content)
    entry = entry.model_copy(
        update=dict(files={**entry.files, "workflow.json": api.sha(content)})
    )
    with pytest.raises(PermissionError, match="manual"):
        prepare(entry)


@pytest.mark.parametrize("placement", ["source_parent", "source_child"])
def test_seal_never_writes_into_overview_source_tree(fixture, tmp_path, placement):
    request = fixture.request.model_copy(update=dict(assignment_discovery=True))
    child = selected_children(plan_week(request))[0]
    batch = api.plan(
        fixture.manifest,
        ["cs50_python"],
        [child.material_id],
        assignment_snapshots=for_week(request),
    )
    archive = tmp_path / "archive"
    archive.mkdir(mode=0o700)
    root = batch.assignment_snapshots[0].path.parent
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    destination = root if placement == "source_parent" else root / "unapproved-catalog"
    with pytest.raises(ValueError, match="overview source"):
        api.seal(batch, archive, destination, api.Approvals())
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    if placement == "source_child":
        assert not destination.exists()
