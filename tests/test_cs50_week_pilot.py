"""Explicit three-HTML selection using the existing pilot and C16/C18 stack."""

import json
import time
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from test_cs50_pilot import environment as environment
from test_cs50_pilot import offline as offline
from test_cs50_pilot import simulated_bootstrap, snapshot

from scripts import cs50_pilot as pilot
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.models import TERMINAL, Settings
from src.tools_materials import batch as api


@pytest.fixture
def week(environment, monkeypatch, tmp_path):
    env = environment
    overview = env.snapshots / "cs50_python/week_0.html"
    text = overview.read_text().replace("src0/hello.py", "src0/")
    text = text.replace(
        "</ul></li></ul></main>",
        '</ul></li><li><a href="/python/psets/0/">Problem Set 0</a></li></ul></main>',
    )
    overview.write_text(text)
    manifest = json.loads((env.snapshots / "manifest.json").read_text())
    for page in manifest["courses"][0]["pages"]:
        page["sha256"] = api.sha((env.snapshots / page["file"]).read_bytes())
    (env.snapshots / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(
        pilot,
        "SNAPSHOTS",
        {p["file"]: p["sha256"] for p in manifest["courses"][0]["pages"]},
    )
    all_bindings = api.make_plan(env.snapshots / "manifest.json").materials
    bindings = [b for b in all_bindings if b.format == "html" and api.supported(b)]
    assert len(bindings) == 3
    env.bundle = tmp_path / "week-bundle"
    pilot.export(env.snapshots, env.bundle, [b.source_id for b in bindings])
    target = SimpleNamespace(
        root=env.mounts[0] / "cs50_pilot_week0",
        policy=env.mounts[3] / "week.paths.json",
        token=env.mounts[3] / "week.token",
    )
    simulated_bootstrap(target, monkeypatch)
    env.root, env.policy, env.token = target.root, target.policy, target.token
    pilot.initialize(
        env.bundle, env.root, "synthetic-week-operator", env.token, prepared=True
    )
    batch = pilot.inputs(env.root)[2]
    assert len(batch.materials) == 3
    env.batch = batch
    env.limits = pilot.limits(3)
    env.payloads = {
        b.original_url: (
            '<!doctype html><html><head><meta charset="utf-8"></head><body><main>'
            "<h1>Synthetic material</h1><p>Functions accept arguments.</p>"
            '<ul><li><a href="#code">Contents</a></li></ul>'
            '<pre>def f():\n\tprint("https://example.org/reference héllo '
            + str(i)
            + '")\n</pre>'
            '<a href="#code">Reference only</a></main></body></html>'
        ).encode()
        for i, b in enumerate(batch.materials)
    }
    data = json.loads((env.root / "approvals.json").read_text())
    for row in data["sources"]:
        row.update(
            download=True,
            process=True,
            expected_sha256=api.sha(env.payloads[row["original_url"]]),
        )
        for key in row:
            if key.endswith("_reference"):
                row[key] = "synthetic-week-operator-decision"
    (env.root / "approvals.json").write_text(json.dumps(data))
    env.approvals = api.load_approvals(env.root / "approvals.json")
    env.calls = []
    return env


def download(env, *, failed=None, oversized=None, retry=False, approvals=None):
    def respond(request):
        url = str(request.url)
        env.calls.append(url)
        if url == failed:
            return httpx.Response(503)
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            content=b"x" * (1048576 + 1) if url == oversized else env.payloads[url],
        )

    return api.obtain(
        env.batch,
        env.root / "archive",
        approvals or env.approvals,
        execute=True,
        retry_failed=retry,
        transport=httpx.MockTransport(respond),
        sleep=lambda _: None,
        limits=env.limits,
    )


def seal(env):
    return api.seal(
        env.batch,
        env.root / "archive",
        env.root / "catalog",
        env.approvals,
        limits=env.limits,
    )


def planned(env):
    api.output(
        env.root / "batch.json",
        {
            "batch": env.batch.model_dump(mode="json"),
            "sha256": api.fingerprint(env.batch.model_dump(mode="json")),
        },
    )
    return api.load_batch(env.root / "batch.json")


def test_versioned_week0_explicit_export_contract(tmp_path, capsys):
    resources = [
        pilot.SOURCE,
        "resource:5f51d97877d3ddbc6699e5c9b484c47b601ce15d1373cfdef065d8fad47b5944",
        "resource:1200b44f5efad4c2796fe526c66701859159dc235f6c7d947edf25a9935bdf05",
        "resource:2b18399f3ce8d176b421afd8f3d4b7352851e4e1dcb990821658f9aebd67a80f",
        "resource:959434ab111dd5b875159fa7508d37955d604cdd6c3acc82f7d3133ea34b3a16",
    ]
    snapshots = Path(__file__).resolve().parents[1] / "docs/course_sources/cs50"
    output = tmp_path / "versioned-metadata-only"
    argv = ["export", "--snapshots", str(snapshots), "--output", str(output)]
    for resource in resources:
        argv += ["--resource", resource]
    assert pilot.main(argv) == 0
    assert set(json.loads(capsys.readouterr().out)["source_ids"]) == set(resources)
    batch = pilot.bundle(output)
    assert len(batch.materials) == 5
    assert sum(b.format == "html" for b in batch.materials) == 3
    assert sum(b.format == "pdf" for b in batch.materials) == 2
    assert batch.source_origin == "official"  # Discovery provenance, no real content.
    assert not (output / "raw.source").exists()
    assert pilot.main(argv) == 2  # Exclusive publication, no overwrite.


@pytest.mark.parametrize("count", [0, 9])
def test_binding_list_rejected_before_model_construction(week, count):
    path = week.root / "reports/invalid-bindings.json"
    path.write_text(json.dumps([{}] * count))
    with pytest.raises(pilot.Blocked, match="one_to_eight"):
        pilot.declared(week.batch.manifest, path)


def test_three_explicit_html_setup_capacity_preview_and_readiness(week):
    env = week
    assert env.limits.reserve_bytes == 5 * 1024**3
    assert env.limits.max_materials == 3
    assert pilot.preflight(env.root, "plan")["max_raw_bytes"] == 1048576
    batch = planned(env)
    assert batch == env.batch
    result = api.obtain(batch, env.root / "archive", env.approvals, limits=env.limits)
    assert len(result["materials"]) == 3 and not env.calls
    assert all(row["status"] == "selected" for row in result["materials"])
    assert all(row["download_approved"] for row in result["materials"])
    denied = api.obtain(batch, env.root / "archive", api.Approvals(), limits=env.limits)
    assert not any(row["download_approved"] for row in denied["materials"])
    assert download(env)["execution_requested"]
    assert all(
        row["status"] == "verified"
        for row in pilot.preflight(env.root, "download")["archive"]["materials"]
    )
    assert len(seal(env)["catalog"]) == 3
    assert len(pilot.configure(env.root)["source_refs"]) == 3
    assert pilot.preflight(env.root, "process")["status"] == "ready"
    settings = Settings.model_validate_json((env.root / "controller.json").read_bytes())
    assert settings.max_jobs == 9 and settings.max_queued == settings.max_parallel == 1
    with pytest.raises(FileExistsError):
        seal(env)


@pytest.mark.parametrize("problem", ["http", "oversize", "missing_grant"])
def test_partial_download_only_approved_sources_and_explicit_retry(week, problem):
    env = week
    target = env.batch.materials[1]
    before = snapshot(env.root / "inputs")
    approvals = env.approvals
    if problem == "missing_grant":
        approvals = approvals.model_copy(
            update={
                "sources": tuple(
                    a for a in approvals.sources if a.material_id != target.material_id
                )
            }
        )
    result = download(
        env,
        failed=target.original_url if problem == "http" else None,
        oversized=target.original_url if problem == "oversize" else None,
        approvals=approvals,
    )
    assert [r["status"] for r in result["materials"]].count("verified") == 2
    assert target.original_url not in env.calls if problem == "missing_grant" else True
    count = len(env.calls)
    again = download(env, approvals=approvals)
    if problem != "missing_grant":
        assert len(env.calls) == count
        assert again["materials"][1]["status"] == "blocked"
    recovered = download(env, retry=True)
    assert all(r["status"] == "verified" for r in recovered["materials"])
    assert recovered["materials"][0]["reused"] and recovered["materials"][2]["reused"]
    assert snapshot(env.root / "inputs") == before
    assert len(seal(env)["catalog"]) == 3


def test_batch_approval_and_selection_limits_fail_closed(week):
    env = week
    doc = json.loads((env.root / "approvals.json").read_text())
    doc["sources"][2]["process"] = False
    (env.root / "approvals.json").write_text(json.dumps(doc))
    with pytest.raises(pilot.Blocked, match="approval_missing"):
        pilot.preflight(env.root, "plan")
    with pytest.raises(ValueError, match="material count"):
        api.obtain(
            env.batch, env.root / "archive", env.approvals, limits=pilot.limits()
        )
    with pytest.raises(pilot.Blocked):
        pilot.selected(env.batch.manifest, [env.batch.materials[0].source_id] * 2)
    with pytest.raises(pilot.Blocked):
        pilot.selected(env.batch.manifest, ["unselected"] * 9)
    media = next(
        b
        for b in api.make_plan(env.batch.manifest).materials
        if b.role == "lecture_video"
    )
    with pytest.raises(pilot.Blocked, match="supported_week_zero"):
        pilot.selected(env.batch.manifest, [media.source_id])


def test_pending_report_scope_no_false_quality_and_catalog_row_consistency(week):
    env = week
    download(env)
    planned(env)
    document = seal(env)
    pilot.configure(env.root)
    ref = next(iter(document["catalog"]))
    result = api.control(
        env.root / "controller.json",
        env.token,
        env.root / "catalog/catalog.json",
        "report",
        [ref],
        limits=env.limits,
    )
    assert result["summary"]["material_count"] == 1
    assert result["summary"]["accounted_materials"] == 0
    assert result["summary"]["materials"][0]["accounting"] is None
    assert result["summary"]["materials"][0]["source_ref"] == ref
    wrong_token = env.root / "reports/wrong.token"
    wrong_token.write_text("synthetic-unrecognized-token-for-negative-test\n")
    with pytest.raises(PermissionError):
        api.control(
            env.root / "controller.json",
            wrong_token,
            env.root / "catalog/catalog.json",
            "report",
            limits=env.limits,
        )
    document["materials"][0]["source_ref"] = "foreign_ref"
    document["sha256"] = api.fingerprint(
        {k: v for k, v in document.items() if k != "sha256"}
    )
    (env.root / "catalog/catalog.json").write_text(json.dumps(document))
    with pytest.raises(pilot.Blocked, match="rows_inconsistent"):
        pilot.catalog(env.root, env.batch, env.approvals)


@pytest.mark.parametrize("partial", [False, "cancelled", "failed"])
def test_actual_three_html_workflows_report_code_preservation_and_resume(week, partial):
    env = week
    if partial == "failed":
        url = env.batch.materials[1].original_url
        env.payloads[url] = b"<html><main></main></html>"
        sources = tuple(
            a.model_copy(
                update={"expected_sha256": api.sha(env.payloads[a.original_url])}
            )
            for a in env.approvals.sources
        )
        env.approvals = env.approvals.model_copy(update={"sources": sources})
        (env.root / "approvals.json").write_text(env.approvals.model_dump_json())
    assert all(r["status"] == "verified" for r in download(env)["materials"])
    planned(env)
    document = seal(env)
    pilot.configure(env.root)
    settings = Settings.model_validate_json((env.root / "controller.json").read_bytes())
    controller = Controller(settings)
    actor = controller.authenticate("Bearer " + env.token.read_text().strip())
    worker = Executor(settings)
    refs = list(document["catalog"])
    first_job = None
    try:
        for i, ref in enumerate(refs):
            result = api.control(
                env.root / "controller.json",
                env.token,
                env.root / "catalog/catalog.json",
                "execute",
                [ref],
                confirm=True,
                limits=env.limits,
            )
            job_id = result["workflows"][0]["job"]["job_id"]
            if i == 0:
                first_job = job_id
            if partial == "cancelled" and i == 1:
                controller.cancel(actor, job_id)
                worker.step()
                assert controller.get(actor, job_id).status == "cancelled"
                continue
            deadline = time.monotonic() + 60
            while controller.get(actor, job_id).status not in TERMINAL:
                assert time.monotonic() < deadline
                worker.step()
                time.sleep(0.05)
            assert controller.get(actor, job_id).status == (
                "failed" if partial == "failed" and i == 1 else "completed"
            )
            if i == 0:
                worker.close()
                worker = Executor(settings)  # Reconcile same persistent batch root.
        result = api.control(
            env.root / "controller.json",
            env.token,
            env.root / "catalog/catalog.json",
            "report",
            limits=env.limits,
        )
        summary = result["summary"]
        assert summary["material_count"] == 3
        assert summary["accounted_materials"] == (2 if partial else 3)
        assert summary["status_counts"] == (
            {"completed": 2, partial: 1} if partial else {"completed": 3}
        )
        for row in summary["materials"]:
            assert row["execution_supported"] is row["knowledge_fact_verified"] is False
            if row["accounting"] is not None:
                account = row["accounting"]
                assert account["code_blocks"] == 1 and account["code_preserved"]
                assert (
                    account["excluded_blocks"]
                    and account["source_origin"] == "synthetic"
                )
        resumed = api.control(
            env.root / "controller.json",
            env.token,
            env.root / "catalog/catalog.json",
            "resume",
            [refs[0]],
            confirm=True,
            limits=env.limits,
        )
        assert resumed["workflows"][0]["job"]["job_id"] == first_job
        assert len(controller.store.all()) == 3
        assert api.summarize(settings, result) == summary
        if not partial:
            handoff = next(
                o
                for o in result["workflows"][0]["report"]["output_refs"]
                if o["kind"] == "handoff"
            )
            path = settings.root / handoff["path"]
            path.write_bytes(path.read_bytes() + b" ")
            changed = api.summarize(settings, result)
            ref = result["workflows"][0]["source_ref"]
            assert next(r for r in changed["materials"] if r["source_ref"] == ref)[
                "errors"
            ] == ["handoff_verification_failed"]
            # Restore exact synthetic bytes so the final readonly preflight still applies.
            path.write_bytes(path.read_bytes()[:-1])
    finally:
        worker.close()
    # Stopped-worker readonly preflight recognizes the bounded multi-job history.
    assert pilot.preflight(env.root, "process")["status"] == "ready"
