"""Course preflight uses real B5 contracts, synthetic bytes and read-only exports."""

import json
import os
import socket
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.cs50_course import main
from src.job_control.models import fingerprint
from src.model_materials.course import (
    ApprovalPolicy,
    CourseReport,
    CourseRequest,
    ReferenceAcceptance,
    SourceReview,
)
from src.model_materials.week import ProfiledWeekRequest, WeekLimits
from src.tools_materials import batch as api
from src.tools_materials.course import (
    contracts_revision,
    plan_course,
    policy_grant,
    profile_format,
)
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.processing import MaterialProcessor
from src.tools_materials.profiles import load_profile
from src.tools_materials.week import plan_week, prepare_material_batches, routing
from tests.test_cs50_week_materials import completed_materials, ready
from tests.test_cs50_week_materials import fixture as fixture  # noqa: F401


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*a, **k):
        pytest.fail("No network or acquisition in course planner")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def multi(fixture):
    root = fixture.root
    manifest = json.loads(fixture.manifest.read_text())
    index = root / "cs50_python/index.html"
    index.write_text(
        index.read_text().replace(
            "</nav>", '<a href="/python/weeks/1/">Week 1</a></nav>'
        )
    )
    page = root / "cs50_python/week1.html"
    text = (root / "cs50_python/week0.html").read_text()
    page.write_text(
        text.replace("/0/", "/1/")
        .replace("src0", "src1")
        .replace("lecture0", "lecture1")
        .replace("Week 0", "Week 1")
        .replace("Problem Set 0", "Problem Set 1")
    )
    pset = root / "cs50_python/pset1.html"
    pset.write_text(
        (root / "cs50_python/pset0.html").read_text().replace("Set 0", "Set 1")
    )
    manifest["courses"][0]["pages"].extend(
        [
            dict(
                file="cs50_python/week1.html",
                url="https://cs50.harvard.edu/python/weeks/1/",
                role="week_overview",
            ),
            dict(
                file="cs50_python/pset1.html",
                url="https://cs50.harvard.edu/python/psets/1/",
                role="assignment",
            ),
        ]
    )
    for p in manifest["courses"][0]["pages"]:
        p["sha256"] = api.sha((root / p["file"]).read_bytes())
    fixture.manifest.write_text(json.dumps(manifest))
    fixture.profile = load_profile(fixture.manifest, "cs50_python")
    return fixture


def reference(profile, **changes):
    return ReferenceAcceptance(
        reference="synthetic-reviewed-reference",
        course_id=profile.course_id,
        profile_format_sha256=profile_format(profile),
        adapter_sha256=profile.adapter_sha256,
        contracts_sha256=contracts_revision(),
        material_types=("html", "pdf", "transcript"),
        infrastructure_revision="fixture-infra-v1",
    ).model_copy(update=changes)


def request(f, **changes):
    return CourseRequest(
        manifest=f.manifest,
        course_id="cs50_python",
        profile=f.profile,
        weeks=("0", "1"),
        reference=reference(f.profile),
        evaluated_at=1000,
        infrastructure_revision="fixture-infra-v1",
        source_origin="synthetic",
    ).model_copy(update=changes)


def inventory(f, key):
    return plan_week(
        ProfiledWeekRequest(
            manifest=f.manifest, course_id="cs50_python", week=key, profile=f.profile
        )
    )


def approved(f, tmp_path, *, keys=("0", "1"), role="notes"):
    tmp_path.mkdir(parents=True, exist_ok=True)
    inputs, reviews = [], {}
    for key in keys:
        rows = [
            r
            for r in inventory(f, key).resources
            if r.binding.role == role and not r.parent_resource_ids
        ]
        assert len(rows) == 1
        row = rows[0]
        source = tmp_path / (row.material_id.split(":")[-1] + ".html")
        raw = b'<main><h1>Reviewed source</h1><p>Text.</p><pre>print("offline")</pre></main>'
        source.write_bytes(raw)
        from src.model_materials.week import LocalSource

        inputs.append(
            ProfiledWeekRequest(
                manifest=f.manifest,
                course_id="cs50_python",
                week=key,
                profile=f.profile,
                mode="process_existing",
                source_origin="synthetic",
                material_types=("html",),
                material_ids=(row.material_id,),
                local_sources=(
                    LocalSource(
                        material_id=row.material_id,
                        path=source,
                        expected_sha256=api.sha(raw),
                    ),
                ),
                available_bytes=100 * 1024**3,
                available_memory_mb=768,
            )
        )
        reviews[row.material_id] = SourceReview(
            material_id=row.material_id,
            source_id=row.resource_id,
            original_url=row.binding.original_url,
            sections=row.binding.resource.section_keys,
            role=row.binding.role,
            format=row.binding.format,
            conditions_sha256="b" * 64,
            expected_sha256=api.sha(raw),
            process=True,
        )
    policy = ApprovalPolicy(
        policy_id="synthetic-policy",
        course_id="cs50_python",
        purpose="synthetic-offline-processing",
        origins=("https://cs50.harvard.edu",),
        conditions_sha256="b" * 64,
        valid_from=500,
        expires_at=1500,
        status_checked_at=990,
        revoked=False,
        approval_reference="synthetic-approval",
        license_review_reference="synthetic-license",
        robots_review_reference="synthetic-access",
        retention_reference="synthetic-retention",
        revocation_reference="synthetic-revocation",
        sources=tuple(reviews.values()),
    )
    return request(f, weeks=keys, week_inputs=tuple(inputs), policies=(policy,))


def reasons(report):
    return " ".join(
        c.reason for c in report.preflight.checks if c.status in {"fail", "unknown"}
    )


def test_multiweek_plan_deterministic_and_no_execution(multi, tmp_path, monkeypatch):
    req = approved(multi, tmp_path)
    monkeypatch.setattr(
        MaterialDownloader, "obtain", lambda *a, **k: pytest.fail("No obtain")
    )
    monkeypatch.setattr(
        MaterialProcessor, "parse", lambda *a, **k: pytest.fail("No parser")
    )
    one = plan_course(req)
    assert one == plan_course(req)
    assert len(one.weeks) == 2 and not any(w.error for w in one.weeks)
    assert one.counts["approved_sources"] == 2
    assert one.preflight.decision == "ready_with_warnings"
    assert (
        not one.execution_supported and one.preflight.production_decision == "blocked"
    )
    assert one.pilot_category == 1 and not one.subject_matter_complete
    assert all(w.report.schema_version == 2 for w in one.weeks)
    assert all(u["download"] == "false" for u in one.approvals_used)


def repin(f):
    data = json.loads(f.manifest.read_text())
    for course in data["courses"]:
        for p in course["pages"]:
            p["sha256"] = api.sha((f.root / p["file"]).read_bytes())
    f.manifest.write_text(json.dumps(data))
    f.profile = load_profile(f.manifest, "cs50_python")


def test_duplicate_material_across_weeks_keeps_one_unique_count(multi, tmp_path):
    p = multi.root / "cs50_python/week1.html"
    p.write_text(p.read_text().replace("/python/notes/1/", "/python/notes/0/"))
    repin(multi)
    report = plan_course(approved(multi, tmp_path))
    selected = [r for w in report.weeks for r in w.report.resources if r.selected]
    assert len(selected) == 2 and selected[0].material_id == selected[1].material_id
    assert report.counts["selected"] == 1 and report.counts["approved_sources"] == 1
    assert report.shared_materials[selected[0].material_id] == ("0", "1")
    assert not report.identity_conflicts


def test_identical_url_different_roles_never_merged(multi):
    p = multi.root / "cs50_python/week0.html"
    p.write_text(
        p.read_text().replace(
            "</main>",
            '<ul><li>Problem Set<ul><li><a href="/python/notes/0/">Other role</a></li></ul></li></ul></main>',
        )
    )
    repin(multi)
    report = plan_course(request(multi, mode="discovery_only"))
    rows = [
        r
        for r in report.weeks[0].report.resources
        if r.binding.original_url == "https://cs50.harvard.edu/python/notes/0/"
    ]
    assert len(rows) == 2 and len({r.resource_id for r in rows}) == 2


@pytest.mark.parametrize(
    "field,value",
    [
        ("discovery_adapter", "mit_ocw"),
        ("adapter_version", "99"),
        ("adapter_sha256", "0" * 64),
    ],
)
def test_unknown_adapter_or_revision_blocked(multi, field, value):
    profile = multi.profile.model_copy(update={field: value})
    report = plan_course(request(multi, profile=profile))
    assert all(w.error for w in report.weeks) and report.preflight.decision == "blocked"


def test_unknown_course_and_scope_rejected(multi):
    data = request(multi).model_dump(mode="json")
    data["course_id"] = "mit_unknown"
    with pytest.raises(ValidationError):
        CourseRequest.model_validate(data)
    with pytest.raises(ValueError):
        load_profile(multi.manifest, "mit_unknown")
    data = request(multi).model_dump(mode="json")
    data["weeks"] = ["99"]
    with pytest.raises(ValidationError):
        CourseRequest.model_validate(data)


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"expires_at": 900}, "approval_expired"),
        ({"valid_from": 1100}, "not_yet_valid"),
        ({"revoked": True}, "approval_revoked"),
        ({"status_checked_at": 1}, "revocation_status_stale"),
        ({"status_checked_at": 1100}, "revocation_status_stale"),
        ({"origins": ("https://other.example",)}, "scope_origin"),
        ({"conditions_sha256": "c" * 64}, "conditions_changed"),
    ],
)
def test_policy_expiry_revocation_scope_and_conditions(multi, tmp_path, change, reason):
    req = approved(multi, tmp_path)
    req = req.model_copy(
        update={"policies": (req.policies[0].model_copy(update=change),)}
    )
    r = plan_course(req)
    assert r.preflight.decision == "blocked" and reason in reasons(r)
    assert r.counts["approved_sources"] == 0


def test_missing_approval_and_legacy_grant_cannot_assert_validity(multi, tmp_path):
    req = approved(multi, tmp_path)
    wr = req.week_inputs[0]
    row = next(
        r
        for r in inventory(multi, "0").resources
        if r.material_id == wr.material_ids[0]
    )
    grant, _ = policy_grant(req, row.binding, "0")
    req = req.model_copy(update={"policies": ()})
    report = plan_course(req, api.Approvals(sources=(grant,)))
    assert report.preflight.decision == "blocked"
    assert "unique_explicit_source_policy_review_required" in reasons(report)


def test_no_implicit_flags_or_cross_week_grant(multi, tmp_path):
    req = approved(multi, tmp_path)
    p = req.policies[0]
    review = p.sources[0].model_copy(update={"process": False})
    req = req.model_copy(
        update={"policies": (p.model_copy(update={"sources": (review,)}),)}
    )
    r = plan_course(req)
    assert r.preflight.decision == "blocked" and r.counts["approved_sources"] == 0
    assert "source_process_approval" in reasons(r)


def test_snapshot_hash_mismatch_is_not_a_warning(multi):
    req = request(multi)
    p = multi.root / "cs50_python/week1.html"
    p.write_text(p.read_text() + "changed")
    report = plan_course(req)
    assert report.preflight.decision == "blocked" and all(w.error for w in report.weeks)


def test_source_hash_error_isolated_to_week(multi, tmp_path):
    req = approved(multi, tmp_path)
    req.week_inputs[1].local_sources[0].path.write_bytes(b"changed")
    report = plan_course(req)
    assert not any(w.error for w in report.weeks)
    assert report.weeks[0].report.counts["ready"] == 0  # Live worker unknown.
    assert report.weeks[0].report.resources != report.weeks[1].report.resources
    checks = [
        c
        for c in report.preflight.checks
        if c.code == "material_binding_raw_parser_quality"
    ]
    assert [c.status for c in checks] == ["pass", "fail"]
    assert report.preflight.decision == "blocked"


@pytest.mark.parametrize("selection", ["all", "complete"])
def test_manual_code_never_acquired_with_complete_scope(
    multi, tmp_path, monkeypatch, selection
):
    req = approved(multi, tmp_path)
    req = req.model_copy(update={"week_inputs": (), "selection": selection})
    monkeypatch.setattr(
        MaterialDownloader, "obtain", lambda *a, **k: pytest.fail("Code acquisition")
    )
    from tests.test_cs50_week_materials import grant

    supplied = {
        row.material_id: grant(row.binding, b"manually reviewed code")
        for key in req.weeks
        for row in inventory(multi, key).resources
        if row.acquisition_policy == "manual_only"
    }
    r = plan_course(req, api.Approvals(sources=tuple(supplied.values())))
    codes = [
        row
        for w in r.weeks
        for row in w.report.resources
        if row.acquisition_policy == "manual_only"
    ]
    assert codes and all(row.action in {"reference_only", "blocked"} for row in codes)
    assert all(not row.planned_steps for row in codes)
    assert (
        r.preflight.decision == "blocked"
    )  # No approvals or raws for other selected resources.


@pytest.mark.parametrize(
    "url",
    [
        "https://cdn.cs50.net/python/2022/x/lectures/0/src0/",
        "https://cs50.harvard.edu/python/code/index.html",
        "https://cs50.harvard.edu/python/src/",
        "https://cs50.harvard.edu/python/fake.py",
        "https://cs50.harvard.edu/python/fake.%2570%2579",
        "https://cs50.harvard.edu/python/fake.zip",
    ],
)
def test_misleading_html_and_retry_cannot_bypass_code_policy(multi, url):
    from src.model_materials.materials import MaterialResource

    row = next(r for r in inventory(multi, "0").resources if r.binding.role == "notes")
    raw = row.binding.resource.model_dump(mode="json") | dict(
        original_url=url, role="notes", format="html"
    )
    from src.model_discovery.cs50 import ResourceCandidate

    binding = MaterialResource(
        resource=ResourceCandidate.model_validate(raw),
        original_url=url,
        role="notes",
        format="html",
        lecture_ids=row.binding.lecture_ids,
    )
    assert routing(binding, WeekLimits())[:3] == ("code", "manual_only", "manual_code")


def test_children_and_unsupported_materials_blocked(multi, tmp_path):
    rows = inventory(multi, "0").resources
    child = next(r for r in rows if r.parent_resource_ids)
    wr, grants = ready(multi, [child], tmp_path)
    profiled = ProfiledWeekRequest.model_validate(
        wr.model_dump(exclude={"schema_version"}) | dict(profile=multi.profile)
    )
    report, batches = prepare_material_batches(profiled, grants)
    assert (
        not batches
        and "assignment_child_c18_adapter_not_integrated"
        in next(r for r in report.resources if r.selected).blockers
    )
    bad = profiled.model_copy(
        update={"material_ids": ("material:invented",), "local_sources": ()}
    )
    r = plan_course(request(multi, week_inputs=(bad,)))
    assert r.weeks[0].error and r.weeks[1].report


@pytest.mark.parametrize("changed", ["handoff", "parser", "memory", "disk", "scope"])
def test_quality_contracts_and_limits_fail_closed(multi, tmp_path, changed):
    req = approved(multi, tmp_path)
    blocked = True
    if changed == "handoff":
        req = req.model_copy(update={"minimum_handoff_version": 2})
        from src.tools_lecture.material_handoff import LectureMaterialHandoff

        if LectureMaterialHandoff.model_fields["schema_version"].default == 2:
            blocked = False
    elif changed == "parser":
        req = req.model_copy(
            update={
                "reference": req.reference.model_copy(
                    update={"contracts_sha256": "0" * 64}
                )
            }
        )
    else:
        wr = req.week_inputs[0]
        values = {
            "memory": {"available_memory_mb": 1},
            "disk": {"available_bytes": 1},
            "scope": {"material_ids": (), "selection": "all"},
        }[changed]
        req = req.model_copy(
            update={"week_inputs": (wr.model_copy(update=values), req.week_inputs[1])}
        )
    report = plan_course(req)
    assert (report.preflight.decision == "blocked") is blocked


def test_production_unknown_signals_never_ready(multi, tmp_path):
    req = approved(multi, tmp_path).model_copy(update={"environment": "production"})
    r = plan_course(req)
    assert r.preflight.decision == "blocked"
    assert {
        c.code for c in r.preflight.checks if c.required and c.status == "unknown"
    } >= {"live_worker_queue", "deployment_gate", "persistent_paths_capacity"}


def test_verified_artifact_reuse_and_controlled_resume(multi, tmp_path, monkeypatch):
    old, grants, archive = completed_materials(multi, tmp_path)
    profiled = ProfiledWeekRequest.model_validate(
        old.model_dump(exclude={"schema_version"}) | dict(profile=multi.profile)
    )
    base = approved(multi, tmp_path / "new")
    g = grants.sources[0]
    review = next(s for s in base.policies[0].sources if s.material_id == g.material_id)
    review = review.model_copy(
        update=dict(
            grant_sha256=fingerprint(g.model_dump(mode="json")),
            expected_sha256=g.expected_sha256,
            download=g.download,
            process=g.process,
        )
    )
    policy = base.policies[0].model_copy(update={"sources": (review,)})
    req = request(multi, week_inputs=(profiled,), policies=(policy,))
    before = {p: p.read_bytes() for p in archive.rglob("*") if p.is_file()}
    monkeypatch.setattr(
        MaterialProcessor, "parse", lambda *a, **k: pytest.fail("No reprocessing")
    )
    first = plan_course(req, grants)
    assert (
        first.counts["reused"] == 1 and first.weeks[0].report.scope_processing_complete
    )
    # Missing grants/inputs for week 1 do not erase the completed week 0 evidence.
    assert (
        first.preflight.decision == "blocked"
        and not first.technical_processing_complete
    )
    assert first == plan_course(req, grants)
    revoked = plan_course(
        req.model_copy(
            update={"policies": (policy.model_copy(update={"revoked": True}),)}
        ),
        grants,
    )
    assert revoked.counts["reused"] == 0 and "approval_revoked" in reasons(revoked)
    changed = profiled.model_copy(update={"limits": WeekLimits(max_bytes=524288)})
    assert (
        plan_course(req.model_copy(update={"week_inputs": (changed,)}), grants).counts[
            "reused"
        ]
        == 0
    )
    assert {p: p.read_bytes() for p in before} == before


def test_pilot_matrix_accumulates_relevant_changes(multi):
    from src.tools_materials.course import pilot_decision

    req = request(multi)
    assert pilot_decision(req)[0] == 1
    assert (
        pilot_decision(
            req.model_copy(
                update={
                    "reference": req.reference.model_copy(update={"course_id": "cs50x"})
                }
            )
        )[0]
        == 2
    )
    assert (
        pilot_decision(req.model_copy(update={"material_types": ("html", "media")}))[0]
        == 3
    )
    assert (
        pilot_decision(
            req.model_copy(
                update={
                    "reference": req.reference.model_copy(
                        update={"contracts_sha256": "0" * 64}
                    )
                }
            )
        )[0]
        == 4
    )
    assert (
        pilot_decision(req.model_copy(update={"infrastructure_revision": "changed"}))[0]
        == 5
    )


def test_cli_json_exit_codes_and_no_execute(multi, tmp_path, capsys):
    req = approved(multi, tmp_path)
    path = tmp_path / "request.json"
    path.write_text(req.model_dump_json())
    assert main(["preflight", "--request", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["production_decision"] == "blocked"
    assert (
        main(
            [
                "plan",
                "--manifest",
                str(multi.manifest),
                "--course",
                "cs50_python",
                "--weeks",
                "0",
                "1",
            ]
        )
        == 0
    )
    assert len(json.loads(capsys.readouterr().out)["weeks"]) == 2
    assert (
        main(
            [
                "preflight",
                "--manifest",
                str(multi.manifest),
                "--course",
                "cs50_python",
                "--weeks",
                "0",
                "1",
            ]
        )
        == 3
    )
    assert json.loads(capsys.readouterr().out)["decision"] == "blocked"
    assert main(["report", "--request", str(path), "--weeks", "0"]) == 2
    assert "error" in json.loads(capsys.readouterr().out)
    with pytest.raises(SystemExit):
        main(["execute", "--request", str(path)])


def test_reports_reject_contradictory_counts_and_scope(multi, tmp_path):
    r = plan_course(approved(multi, tmp_path))
    data = r.model_dump(mode="json")
    data["counts"]["processed"] = 99
    with pytest.raises(ValidationError):
        CourseReport.model_validate(data)
    data = r.model_dump(mode="json")
    data["preflight"]["decision"] = "blocked"
    with pytest.raises(ValidationError):
        CourseReport.model_validate(data)


def test_real_export_child_ids_still_explicitly_blocked():
    from src.model_materials.week import DiscoverySnapshot

    root = os.environ.get("CS50_WEEK0_QUALITY_EXPORT")
    if not root:
        pytest.skip("Operator originals not explicitly supplied")
    root = Path(root)
    before = {
        p: p.read_bytes()
        for folder in ("material_01", "material_02")
        for p in (root / folder).iterdir()
        if p.is_file()
    }
    manifest = Path("docs/course_sources/cs50/manifest.json").absolute()
    profile = load_profile(manifest, "cs50_python")
    raw = root / "material_02/original.html"
    wr = ProfiledWeekRequest(
        manifest=manifest,
        profile=profile,
        discovery_exports=(
            DiscoverySnapshot(
                label="operator/pset0.html",
                path=raw,
                original_url="https://cs50.harvard.edu/python/psets/0/",
                sha256=api.sha(raw.read_bytes()),
            ),
        ),
    )
    report = plan_week(wr)
    tasks = [r for r in report.resources if r.parent_resource_ids]
    stored = json.loads(
        Path("docs/deployment/c26a/week0_resources.v1.json").read_text()
    )
    ids = {r["resource_id"] for r in stored["resources"] if r["parent_resource_ids"]}
    assert len(tasks) == 5 and {r.resource_id for r in tasks} == ids
    assert all(
        "assignment_child_not_in_existing_c18_discovery_graph" in r.limitations
        for r in tasks
    )
    assert {p: p.read_bytes() for p in before} == before


def test_known_second_course_and_multi_course_scope(multi):
    from src.tools_materials.course import plan_courses

    data = json.loads(multi.manifest.read_text())
    first = data["courses"][0]
    pages = []
    for page in first["pages"]:
        copy = dict(page)
        copy["file"] = page["file"].replace("cs50_python/", "cs50x/")
        copy["url"] = page["url"].replace("/python/", "/x/")
        target = multi.root / copy["file"]
        target.parent.mkdir(exist_ok=True)
        target.write_text(
            (multi.root / page["file"]).read_text().replace("/python/", "/x/")
        )
        pages.append(copy)
    data["courses"].append(
        dict(course_id="cs50x", source_url="https://cs50.harvard.edu/x/", pages=pages)
    )
    multi.manifest.write_text(json.dumps(data))
    repin(multi)
    xprofile = load_profile(multi.manifest, "cs50x")
    xrequest = CourseRequest(
        manifest=multi.manifest,
        profile=xprofile,
        course_id="cs50x",
        weeks=("0", "1"),
        mode="discovery_only",
        reference=reference(multi.profile),
        infrastructure_revision="fixture-infra-v1",
    )
    reports = plan_courses((request(multi, mode="discovery_only"), xrequest))
    assert len(reports) == 2 and reports[1].pilot_category == 2
    assert all(w.report and w.report.course_id == "cs50x" for w in reports[1].weeks)
    with pytest.raises(ValueError):
        plan_courses((xrequest, xrequest))


@pytest.mark.parametrize("fmt", ["srt", "txt"])
def test_existing_transcript_importer_supports_bound_week_one(
    multi, tmp_path, monkeypatch, fmt
):
    from types import SimpleNamespace

    from src.tools_materials import transcripts
    from src.tools_materials.capacity import CapacityLimits
    from tests.test_cs50_week_materials import grant

    monkeypatch.setattr(
        "shutil.disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3)
    )
    row = next(r for r in inventory(multi, "1").resources if r.binding.format == fmt)
    raw = (
        b"1\n00:00:02,000 --> 00:00:04,000\nWeek one\n\n"
        if fmt == "srt"
        else b"Week one without timestamps.\n"
    )
    path = tmp_path / ("local." + fmt)
    path.write_bytes(raw)
    batch = api.plan(multi.manifest, ["cs50_python"], [row.material_id], synthetic=True)
    binding = batch.materials[0]
    result = transcripts.run(
        batch,
        tmp_path / "archive",
        api.Approvals(sources=(grant(binding, raw),)),
        {row.resource_id: path},
        action="import",
        limits=CapacityLimits(
            reserve_bytes=5 * 1024**3, archive_bytes=64 * 1048576, max_materials=1
        ),
    )
    assert result["materials"][0]["status"] == "processed"
    folder = tmp_path / "archive" / row.material_id.split(":")[-1]
    receipt = json.loads((folder / "receipt.json").read_bytes())
    payload = json.loads((folder / "transcript.json").read_bytes())
    assert receipt["lecture"]["lecture_no"] == "1"
    assert payload["segments"][0]["start"] == (2.0 if fmt == "srt" else None)


def test_manual_only_scope_requires_operator_import(multi):
    row = next(
        r
        for r in inventory(multi, "0").resources
        if r.acquisition_policy == "manual_only"
    )
    wr = ProfiledWeekRequest(
        manifest=multi.manifest,
        course_id="cs50_python",
        profile=multi.profile,
        week="0",
        mode="plan",
        source_origin="synthetic",
        material_ids=(row.material_id,),
    )
    report = plan_course(request(multi, weeks=("0",), week_inputs=(wr,)))
    assert report.preflight.decision == "operator_action_required"
    assert report.counts["approved_sources"] == 0


def test_invalid_clock_and_unknown_review_never_grant(multi, tmp_path):
    req = approved(multi, tmp_path)
    assert "evaluation_time_unknown" in reasons(
        plan_course(req.model_copy(update={"evaluated_at": None}))
    )
    policy = req.policies[0]
    review = policy.sources[0].model_copy(update={"material_id": "material:unobserved"})
    changed = req.model_copy(
        update={"policies": (policy.model_copy(update={"sources": (review,)}),)}
    )
    assert plan_course(changed).counts["approved_sources"] == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"queued_jobs": 1, "running_jobs": 1},
        {"worker_instances": 2},
        {"worker_instances": 0},
        {"observed_at": 1},
        {"observed_at": 1100},
    ],
)
def test_full_queue_unknown_topology_and_stale_observations(multi, tmp_path, changes):
    from src.model_materials.course import QueueObservation

    req = approved(multi, tmp_path)
    values = dict(
        queued_jobs=0,
        running_jobs=0,
        worker_instances=1,
        observed_at=990,
        reference="synthetic-controller-snapshot",
    )
    values.update(changes)
    req = req.model_copy(update={"queue_observation": QueueObservation(**values)})
    report = plan_course(req)
    assert report.preflight.decision == "blocked"
    assert next(
        c for c in report.preflight.checks if c.code == "planning_queue"
    ).status in {"unknown", "fail"}


def test_unknown_material_and_foreign_evidence_are_explicit_week_errors(multi):
    from src.model_materials.week import WorkflowReference

    rows = inventory(multi, "0").resources
    unknown = next(r for r in rows if r.category == "unknown")
    wr = ProfiledWeekRequest(
        manifest=multi.manifest,
        profile=multi.profile,
        mode="plan",
        source_origin="synthetic",
        material_types=("html",),
        material_ids=(unknown.material_id,),
    )
    report = plan_course(request(multi, week_inputs=(wr,)))
    assert report.weeks[0].error and report.weeks[1].report
    ref = WorkflowReference(
        material_id="material:invented",
        controller_root=multi.root,
        job_id="job_" + "a" * 32,
        relative_path="jobs/job_" + "a" * 32 + "/results/report.json",
        sha256="0" * 64,
    )
    wr = wr.model_copy(update={"material_ids": (), "workflow_references": (ref,)})
    assert plan_course(request(multi, week_inputs=(wr,))).weeks[0].error


def test_oversized_and_duplicate_week_scopes_not_truncated(multi):
    for weeks in (("0",) * 2, tuple(str(i) for i in range(9))):
        with pytest.raises(ValidationError):
            CourseRequest.model_validate(request(multi).model_dump() | {"weeks": weeks})


def test_missing_revocation_decision_is_unknown_not_approved(multi, tmp_path):
    policy = approved(multi, tmp_path).policies[0].model_dump()
    del policy["revoked"]
    with pytest.raises(ValidationError):
        ApprovalPolicy.model_validate(policy)
