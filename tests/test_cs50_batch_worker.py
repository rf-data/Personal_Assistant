"""C26 synthetic archive -> C18 -> C16; no real source or host access."""

import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pymupdf
import pytest
import yaml

from scripts.cs50_workflow_demo import inputs
from scripts.job_control_demo import DEMO_TOKEN
from src.job_control.controller import Controller
from src.job_control.models import TERMINAL, Identity, Settings, fingerprint
from src.job_control.operations import backup, fence, restore
from src.model_materials.materials import ArtifactReceipt, NormalizedDocument
from src.tools_materials import batch as api
from src.tools_materials.capacity import CapacityLimits
from src.tools_materials.processing import make_plan
from src.workflows.models import State
from src.workflows.state import load

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("Unapproved network access")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def scope(tmp_path, private_umask):
    inputs(tmp_path / "snapshots")
    overview = tmp_path / "snapshots/cs50_python/week0.html"
    overview.write_text(
        overview.read_text().replace(
            "</ul></li></ul></main>",
            '<li><a href="/python/2022/notes/0/lecture0.pdf">Slides</a></li></ul></li></ul></main>',
        )
    )
    manifest = tmp_path / "snapshots/manifest.json"
    m = json.loads(manifest.read_text())
    for page in m["courses"][0]["pages"]:
        page["sha256"] = api.sha((manifest.parent / page["file"]).read_bytes())
    manifest.write_text(json.dumps(m))
    bindings = [
        b
        for b in make_plan(manifest).materials
        if b.role in {"notes", "slides", "source_code"}
    ]
    assert {b.format for b in bindings} == {"html", "pdf", "py"}
    batch = api.plan(
        manifest, ["cs50_python"], [b.source_id for b in bindings], synthetic=True
    )
    pdf = pymupdf.open()
    for _ in range(2):
        page = pdf.new_page()
        for y in range(50, 700, 20):
            page.insert_text((50, y), "Synthetic processing worker document")
    pdf_data = pdf.tobytes(no_new_id=True)
    pdf.close()
    payloads = {
        b.original_url: pdf_data
        if b.format == "pdf"
        else b"<html><main><h1>Synthetic notes</h1><p>Functions accept arguments.</p></main></html>"
        if b.format == "html"
        else b'print("synthetic source")\n'
        for b in batch.materials
    }
    approvals = api.Approvals(
        sources=tuple(
            api.SourceApproval(
                material_id=b.material_id,
                source_id=b.source_id,
                course_id=b.resource.course_id,
                original_url=b.original_url,
                approval_reference="synthetic-test-operator",
                usage_reference="synthetic-test-purpose",
                license_review_reference="synthetic-test-license",
                robots_review_reference="synthetic-test-robots",
                retention_reference="synthetic-test-retention",
                revocation_reference="synthetic-test-revocation",
                download=True,
                process=True,
                expected_sha256=api.sha(payloads[b.original_url]),
            )
            for b in batch.materials
        )
    )
    archive = tmp_path / "archive"
    archive.mkdir(mode=0o700)
    calls = []

    def respond(request):
        calls.append(str(request.url))
        assert request.headers["Accept-Encoding"] == "identity"
        data = payloads[str(request.url)]
        content_type = (
            "application/pdf"
            if data.startswith(b"%PDF")
            else "text/html"
            if data.startswith(b"<html")
            else "text/plain"
        )
        return httpx.Response(200, content=data, headers={"Content-Type": content_type})

    return dict(
        tmp=tmp_path,
        batch=batch,
        archive=archive,
        approvals=approvals,
        transport=httpx.MockTransport(respond),
        calls=calls,
        payloads=payloads,
    )


def obtain(scope):
    return api.obtain(
        scope["batch"],
        scope["archive"],
        scope["approvals"],
        execute=True,
        transport=scope["transport"],
        sleep=lambda _n: None,
    )


def test_explicit_plan_preview_no_writes_and_hash_binding(scope):
    path = scope["tmp"] / "batch.json"
    batch = scope["batch"]
    api.output(
        path,
        dict(
            batch=batch.model_dump(mode="json"),
            sha256=fingerprint(batch.model_dump(mode="json")),
        ),
    )
    assert api.load_batch(path) == batch
    result = api.obtain(batch, scope["tmp"] / "not-created", api.Approvals())
    assert all(r["status"] == "selected" for r in result["materials"])
    assert not (scope["tmp"] / "not-created").exists() and not scope["calls"]
    with pytest.raises(FileExistsError):
        api.output(path, {})
    (batch.manifest.parent / "cs50_python/week0.html").write_bytes(b"changed")
    with pytest.raises(ValueError, match="Snapshot bytes"):
        api.load_batch(path)


def test_download_idempotency_receipts_rate_and_expected_hash(scope):
    sleeps = []
    result = api.obtain(
        scope["batch"],
        scope["archive"],
        scope["approvals"],
        execute=True,
        transport=scope["transport"],
        sleep=sleeps.append,
    )
    assert len(scope["calls"]) == 3 and sleeps == [2.0, 2.0]
    assert all(
        r["status"] == "verified" and not r["reused"] for r in result["materials"]
    )
    again = obtain(scope)
    assert len(scope["calls"]) == 3
    assert all(r["reused"] for r in again["materials"])
    for row in result["materials"]:
        assert row["raw_sha256"] == api.sha(scope["payloads"][row["original_url"]])
    wrong = scope["approvals"].model_copy(
        update={
            "sources": tuple(
                a.model_copy(update={"expected_sha256": "f" * 64})
                for a in scope["approvals"].sources
            )
        }
    )
    bad = api.obtain(scope["batch"], scope["archive"], wrong, execute=True)
    assert all(r["status"] == "failed" for r in bad["materials"])
    assert len(scope["calls"]) == 3


@pytest.mark.parametrize("change", ["missing", "url", "course", "permission"])
def test_unapproved_sources_never_contact_transport(scope, change):
    grants = scope["approvals"]
    updates = (
        {"original_url": "https://example.com/"}
        if change == "url"
        else {"course_id": "cs50_ai"}
        if change == "course"
        else {"download": False}
    )
    sources = (
        ()
        if change == "missing"
        else tuple(a.model_copy(update=updates) for a in grants.sources)
    )
    result = api.obtain(
        scope["batch"],
        scope["archive"],
        grants.model_copy(update=dict(sources=sources)),
        execute=True,
        transport=scope["transport"],
    )
    assert all(r["status"] == "blocked" for r in result["materials"])
    assert not scope["calls"]


def test_failed_download_requires_explicit_retry_and_has_no_automatic_retry(scope):
    calls, sleeps = [], []

    def fail(request):
        calls.append(str(request.url))
        return httpx.Response(429)

    result = api.obtain(
        scope["batch"],
        scope["archive"],
        scope["approvals"],
        execute=True,
        transport=httpx.MockTransport(fail),
        sleep=sleeps.append,
    )
    assert len(calls) == 3 and sleeps == [2.0, 2.0]
    assert all(r["status"] == "failed" for r in result["materials"])
    assert all(r["status"] == "blocked" for r in obtain(scope)["materials"])
    assert not scope["calls"]
    retried = api.obtain(
        scope["batch"],
        scope["archive"],
        scope["approvals"],
        execute=True,
        retry_failed=True,
        transport=scope["transport"],
        sleep=lambda _n: None,
    )
    assert all(r["status"] == "verified" for r in retried["materials"])


def test_catalog_preserves_http_provenance_and_no_overwrite(scope):
    obtain(scope)
    destination = scope["tmp"] / "catalog"
    result = api.seal(scope["batch"], scope["archive"], destination, scope["approvals"])
    assert len(result["catalog"]) == 3
    assert all(r["status"] == "sealed" for r in result["materials"])
    for value in result["catalog"].values():
        entry = api.CatalogEntry.model_validate(value)
        receipt = ArtifactReceipt.model_validate_json(
            (entry.root / "download_receipt.v1.json").read_bytes()
        )
        assert (
            receipt.origin == "http_download"
            and receipt.binding.source_origin == "synthetic"
        )
        assert receipt.raw_sha256 == api.sha((entry.root / "raw.source").read_bytes())
        assert all(
            (entry.root / name).stat().st_mode & 511 == 384 for name in entry.files
        )
    with pytest.raises(FileExistsError):
        api.seal(scope["batch"], scope["archive"], destination, scope["approvals"])


def test_corrupt_raw_blocks_sealing_and_symlinks_rejected(scope):
    obtain(scope)
    first = scope["batch"].materials[0]
    downloader = api.MaterialDownloader(scope["archive"])
    raw, _receipt = downloader.paths(api.reviewed(first))
    raw.write_bytes(b"tampered")
    result = api.seal(
        scope["batch"], scope["archive"], scope["tmp"] / "catalog", scope["approvals"]
    )
    assert result["materials"][0]["status"] == "failed"
    assert len(result["catalog"]) == 2
    link = scope["tmp"] / "symlink"
    link.symlink_to(scope["archive"], target_is_directory=True)
    with pytest.raises(ValueError):
        api.obtain(scope["batch"], link, scope["approvals"], execute=True)


def wait(predicate, timeout=25):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        result = predicate()
        if result:
            return result
        time.sleep(0.002)
    pytest.fail("Synthetic worker condition timed out")


@pytest.mark.parametrize("stop_reason", ["signal", "capacity"])
def test_managed_worker_cancel_restart_resume_and_stopped_backup(scope, stop_reason):
    download_report = obtain(scope)
    catalog = api.seal(
        scope["batch"], scope["archive"], scope["tmp"] / "catalog", scope["approvals"]
    )
    settings = Settings(
        root=scope["tmp"] / "jobs",
        catalog={
            k: api.CatalogEntry.model_validate(v) for k, v in catalog["catalog"].items()
        },
        identities=(
            Identity(
                subject="synthetic-operator",
                role="operator",
                courses=("cs50_python",),
                token_sha256=api.sha(DEMO_TOKEN.encode()),
            ),
        ),
        execution_enabled=True,
        workflows_enabled=True,
    )
    settings.root.mkdir(mode=0o700)
    config = scope["tmp"] / "controller.json"
    token = scope["tmp"] / "operator.token"
    api.output(config, settings.model_dump(mode="json"))
    token.write_text(DEMO_TOKEN)
    token.chmod(0o600)
    catalog_file = scope["tmp"] / "catalog/catalog.json"
    limits_file = scope["tmp"] / "limits.json"
    api.output(limits_file, CapacityLimits().model_dump(mode="json"))
    controller = Controller(settings)
    actor = controller.authenticate("Bearer " + DEMO_TOKEN)
    refs = list(catalog["catalog"])
    pdf_ref = next(
        ref
        for ref, entry in settings.catalog.items()
        if (entry.root / "raw.source").read_bytes().startswith(b"%PDF")
    )

    def start():
        return subprocess.Popen(
            [
                sys.executable,
                "-m",
                "scripts.cs50_worker",
                "--config",
                str(config),
                "--limits",
                str(limits_file),
            ],
            cwd=REPO,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    worker = start()
    try:
        wait(lambda: controller.store.worker_available(settings.worker_ttl))
        api.control(config, token, catalog_file, "execute", [pdf_ref], confirm=True)

        def parsing_started():
            state = load(settings.root, pdf_ref, actor)
            return state and any(
                s.process_id == "material_parsing" and s.status == "running"
                for s in state.report.stages
            )

        wait(parsing_started)
        state = load(settings.root, pdf_ref, actor)
        preserved = {
            o.path: o.sha256
            for s in state.report.stages
            if s.status == "completed"
            for o in s.output_refs
        }
        assert preserved
        job = controller.store.all()[0]
        if stop_reason == "capacity":
            # Sparse own test file: tests the size guard without allocating 2 GiB.
            pressure = settings.root / "synthetic-capacity-pressure"
            with pressure.open("xb") as stream:
                stream.truncate(CapacityLimits().job_bytes + 1)
        else:
            controller.cancel(actor, job.job_id)
            worker.terminate()
        worker.wait(timeout=15)
        if stop_reason == "capacity":
            assert worker.returncode == 2
            pressure.unlink()
        worker.stderr.close()
        worker = start()
        wait(lambda: controller.store.worker_available(settings.worker_ttl))
        wait(lambda: controller.get(actor, job.job_id).status in TERMINAL)
        assert controller.get(actor, job.job_id).status in {"cancelled", "interrupted"}
        result = api.control(
            config, token, catalog_file, "resume", [pdf_ref], confirm=True
        )
        next_id = result["workflows"][0]["job"]["job_id"]
        assert next_id != job.job_id
        wait(lambda: controller.get(actor, next_id).status in TERMINAL)
        assert controller.get(actor, next_id).status == "completed"
        api.control(
            config,
            token,
            catalog_file,
            "execute",
            [r for r in refs if r != pdf_ref],
            confirm=True,
        )
        wait(
            lambda: (
                len(controller.store.all()) == 4
                and all(j.status in TERMINAL for j in controller.store.all())
            )
        )
        # A reserve larger than this test filesystem blocks new work, not diagnosis.
        high_reserve = CapacityLimits(reserve_bytes=1024**4)
        reports = api.control(
            config, token, catalog_file, "report", limits=high_reserve
        )
        assert len(reports["workflows"]) == 3
        assert all(w["report"]["status"] == "completed" for w in reports["workflows"])
        with pytest.raises(ValueError, match="reserve"):
            api.control(
                config,
                token,
                catalog_file,
                "execute",
                refs,
                confirm=True,
                limits=high_reserve,
            )
        again = api.control(config, token, catalog_file, "resume", refs, confirm=True)
        assert len(controller.store.all()) == 4
        assert all(
            s["status"] == "skipped"
            for w in again["workflows"]
            for s in w["report"]["stages"]
        )
        for name, digest in preserved.items():
            assert api.sha((settings.root / name).read_bytes()) == digest
        for w in again["workflows"]:
            for ref in w["report"]["output_refs"]:
                data = (settings.root / ref["path"]).read_bytes()
                assert api.sha(data) == ref["sha256"] and len(data) == ref["size_bytes"]
                if ref["kind"] == "normalized":
                    assert (
                        NormalizedDocument.model_validate_json(
                            data
                        ).binding.source_origin
                        == "synthetic"
                    )
        worker.terminate()
        worker.wait(timeout=15)
        backup(config, scope["tmp"] / "snapshot")
        restored = scope["tmp"] / "restored"
        assert restore(scope["tmp"] / "snapshot", restored)["activated"] is False
        for w in again["workflows"]:
            state = State.model_validate_json(
                (restored / f"workflows/{w['source_ref']}/state.v1.json").read_bytes()
            )
            for ref in state.report.output_refs:
                assert api.sha((restored / ref.path).read_bytes()) == ref.sha256
        evidence = dict(
            schema_version=1,
            kind="c26a_synthetic_process_e2e",
            http_transport="httpx.MockTransport",
            downloads=download_report,
            interrupted_job_id=job.job_id,
            interrupted_status=controller.get(actor, job.job_id).status,
            resumed_job_id=next_id,
            separate_worker_restart=True,
            preserved_committed_output_hashes=preserved,
            workflow_results=again,
            stopped_backup_restore_verified=True,
            image_or_container_tested=False,
            real_downloads=0,
        )
        api.output(
            scope["tmp"] / "synthetic-e2e.json",
            dict(evidence=evidence, sha256=fingerprint(evidence)),
        )
    finally:
        if worker.poll() is None:
            worker.terminate()
            worker.wait(timeout=15)
        worker.stderr.close()


def test_unsupported_media_never_downloaded(scope):
    video = next(
        b
        for b in make_plan(scope["batch"].manifest).materials
        if b.role == "lecture_video"
    )
    batch = scope["batch"].model_copy(update=dict(materials=(video,)))
    result = api.obtain(
        batch,
        scope["archive"],
        scope["approvals"],
        execute=True,
        transport=scope["transport"],
    )
    assert result["materials"][0]["status"] == "unsupported"
    assert not scope["calls"]


def test_oversized_http_response_publishes_no_raw(scope):
    transport = httpx.MockTransport(
        lambda _r: httpx.Response(
            200, content=b"x" * 1048577, headers={"Content-Type": "application/pdf"}
        )
    )
    result = api.obtain(
        scope["batch"],
        scope["archive"],
        scope["approvals"],
        execute=True,
        transport=transport,
        sleep=lambda _n: None,
    )
    assert all(r["status"] == "failed" for r in result["materials"])
    assert not list(scope["archive"].glob("*/raw/source"))


@pytest.mark.parametrize(
    "restriction", ["viewer", "course", "catalog", "fence", "index_digest", "metadata"]
)
def test_control_cannot_bypass_identity_scope_or_maintenance(scope, restriction):
    obtain(scope)
    catalog = api.seal(
        scope["batch"], scope["archive"], scope["tmp"] / "catalog", scope["approvals"]
    )
    entries = {
        k: api.CatalogEntry.model_validate(v) for k, v in catalog["catalog"].items()
    }
    settings = Settings(
        root=scope["tmp"] / "jobs",
        catalog={} if restriction == "catalog" else entries,
        identities=(
            Identity(
                subject="actor",
                role="viewer" if restriction == "viewer" else "operator",
                courses=("cs50_ai",) if restriction == "course" else ("cs50_python",),
                token_sha256=api.sha(DEMO_TOKEN.encode()),
            ),
        ),
        execution_enabled=True,
        workflows_enabled=True,
    )
    settings.root.mkdir(mode=0o700)
    config, token = scope["tmp"] / "controller.json", scope["tmp"] / "token"
    api.output(config, settings.model_dump(mode="json"))
    token.write_text(DEMO_TOKEN)
    token.chmod(0o600)
    catalog_file = scope["tmp"] / "catalog/catalog.json"
    ref = next(iter(entries))
    if restriction == "index_digest":
        data = json.loads(catalog_file.read_text())
        data["sha256"] = "f" * 64
        catalog_file.write_text(json.dumps(data))
    if restriction == "metadata":
        data = json.loads(catalog_file.read_text())
        data["materials"].append(
            dict(course_id="cs50_ai", material_id="hidden", status="unsupported")
        )
        data["sha256"] = fingerprint({k: v for k, v in data.items() if k != "sha256"})
        catalog_file.write_text(json.dumps(data))
        result = api.control(config, token, catalog_file, "preview")
        assert len(result["materials"]) == 3
        assert all(row["course_id"] == "cs50_python" for row in result["materials"])
    elif restriction == "fence":
        with fence(settings.root, exclusive=True), pytest.raises(BlockingIOError):
            api.control(config, token, catalog_file, "execute", [ref], confirm=True)
    else:
        with pytest.raises((PermissionError, ValueError)):
            api.control(config, token, catalog_file, "execute", [ref], confirm=True)
    assert not (settings.root / "jobs.sqlite3").exists()


def test_empty_evidence_is_not_source_approval(scope):
    item = scope["approvals"].sources[0].model_dump()
    item["license_review_reference"] = "  "
    with pytest.raises(ValueError, match="Nonblank"):
        api.SourceApproval.model_validate(item)


def test_published_worker_evidence_is_existing_c18_contract():
    from src.workflows.engine import sealed
    from src.workflows.models import Workflow

    data = json.loads(
        (REPO / "docs/deployment/c26a/synthetic_worker.v1.json").read_bytes()
    )
    evidence = data["evidence"]
    assert data["sha256"] == fingerprint(evidence)
    assert (
        evidence["real_downloads"] == 0
        and evidence["image_or_container_tested"] is False
    )
    assert evidence["http_transport"] == "httpx.MockTransport"
    assert evidence["stopped_backup_restore_verified"] is True
    assert evidence["interrupted_status"] in {"cancelled", "interrupted"}
    for item in evidence["workflow_results"]["workflows"]:
        report = Workflow.model_validate(item["report"])
        assert report == sealed(report) and report.status == "completed"
    assert "/home/" not in json.dumps(data) and "/dev/shm/" not in json.dumps(data)


def test_actual_cli_plan_preview_and_rejected_inputs(scope, capsys):
    from scripts.cs50_batch import main

    path = scope["tmp"] / "cli-batch.json"
    assert (
        main(
            [
                "plan",
                "--manifest",
                str(scope["batch"].manifest),
                "--course",
                "cs50_python",
                "--resource",
                scope["batch"].materials[0].source_id,
                "--synthetic",
                "--output",
                str(path),
            ]
        )
        == 0
    )
    assert api.load_batch(path).source_origin == "synthetic"
    capsys.readouterr()
    archive = scope["tmp"] / "not-created"
    assert main(["download", "--batch", str(path), "--archive", str(archive)]) == 0
    assert not archive.exists() and not scope["calls"]
    capsys.readouterr()
    assert (
        main(
            [
                "seal",
                "--batch",
                str(path),
                "--archive",
                str(archive),
                "--output",
                str(scope["tmp"] / "must-not-exist"),
            ]
        )
        == 2
    )
    assert not (scope["tmp"] / "must-not-exist").exists()
    capsys.readouterr()
    broken = scope["tmp"] / "broken.json"
    broken.write_text('{"SYNTHETIC_SENSITIVE_MARKER":')
    assert main(["download", "--batch", str(broken), "--archive", str(archive)]) == 2
    message = capsys.readouterr().out
    assert "SYNTHETIC_SENSITIVE_MARKER" not in message
    assert json.loads(message)["status"] == "rejected"


def test_compose_profiles_and_runtime_inclusion():
    doc = yaml.safe_load((REPO / "deployment/cs50-worker.compose.yaml").read_text())
    assert doc["services"]["executor"]["network_mode"] == "none"
    assert doc["services"]["offline-cli"]["network_mode"] == "none"
    for service in doc["services"].values():
        assert service["profiles"] and service["user"] == "10001:10001"
        assert service["read_only"] is True and service["cap_drop"] == ["ALL"]
        assert "ports" not in service and "privileged" not in service
        assert service["pull_policy"] == "never"
        assert all(v["bind"]["create_host_path"] is False for v in service["volumes"])
        assert not any("docker.sock" in str(v) for v in service["volumes"])
    downloader = doc["services"]["downloader"]
    assert {v["target"] for v in downloader["volumes"]} == {
        "/run/c26",
        "/run/config/c26-limits.json",
        "/var/lib/personal-assistant/archive",
    }
    dockerfile = (REPO / "deployment/Dockerfile").read_text()
    assert "--frozen --no-dev --no-install-project" in dockerfile
    assert "scripts/cs50_batch.py" in dockerfile
    assert "scripts/cs50_worker.py" in dockerfile
