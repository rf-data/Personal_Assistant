"""C19 uses C18's existing graph, receipts, stale rules and C16 lifecycle."""

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_cs50_workflows import finish, run
from test_pdf_job_control import PROBE, wait_for
from test_pdf_job_control import offline as offline

from scripts.cs50_workflow_demo import inputs, sha
from scripts.job_control_demo import DEMO_TOKEN
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.guardian import REPOSITORY, clean_environment, prctl
from src.job_control.models import TERMINAL, Identity, Settings
from src.model_materials.materials import ArtifactReceipt, NormalizedDocument
from src.workflows.definition import prepare
from src.workflows.engine import sealed
from src.workflows.models import Workflow
from src.workflows.service import inspect, submit
from src.workflows.state import load
from tests.test_cs50_material_pdf import pdf_bytes


def test_published_pdf_example_matches_existing_models_and_hashes():
    data = json.loads(
        (REPOSITORY / "docs/workflows/example-pdf-report.v1.json").read_text()
    )
    report = Workflow.model_validate(data["report"])
    assert report == sealed(report) and report.status == "completed"
    assert len(report.stages) == 5 and data["resume_reused_job"] is True
    (receipt,) = [ArtifactReceipt.model_validate(item) for item in data["pdf_receipts"]]
    assert receipt.binding.source_origin == "synthetic"
    assert receipt.parser.name == "pdf" and receipt.parser.version == "2"
    parsed = next(s for s in report.stages if s.process_id == "material_parsing")
    assert parsed.job_id == data["job"]["job_id"] == report.run_id
    assert (
        next(o.sha256 for o in parsed.output_refs if o.kind == "raw")
        == receipt.raw_sha256
    )
    assert (
        next(o.sha256 for o in parsed.output_refs if o.kind == "normalized")
        == receipt.normalized_sha256
    )


@pytest.fixture
def scope(tmp_path):
    entry = inputs(tmp_path / "inputs", pdf=True)
    # Multipage/image regression fixture, independent of the small public demo.
    name = next(iter(prepare(entry).definition.sources.values()))
    (entry.root / name).write_bytes(pdf_bytes())
    entry = entry.model_copy(
        update=dict(files={n: sha((entry.root / n).read_bytes()) for n in entry.files})
    )
    actor = Identity(
        subject="operator",
        role="operator",
        courses=("cs50_python",),
        token_sha256=sha(DEMO_TOKEN.encode()),
    )
    settings = Settings(
        root=tmp_path / "private",
        catalog=dict(source=entry),
        identities=(actor,),
        execution_enabled=True,
        workflows_enabled=True,
    )
    return SimpleNamespace(settings=settings, actor=actor, entry=entry, tmp=tmp_path)


def test_pdf_preview_success_skip_handoff_and_original_provenance(scope):
    original = {n: (scope.entry.root / n).read_bytes() for n in scope.entry.files}
    preview, prepared, _ = inspect(
        scope.settings, scope.actor, "source", "workflow_test"
    )
    assert not scope.settings.root.exists()
    (config,) = prepared.parsers.values()
    assert config.name == "pdf" and config.version == "2" and config.max_pages == 20
    assert len(preview.stages) == 5 and not any(
        s.missing_inputs for s in preview.stages
    )
    executor = Executor(scope.settings)
    try:
        job = run(scope, executor)
        assert job.status == "completed", job.error
        report, _, _ = inspect(scope.settings, scope.actor, "source", "workflow_test")
        assert report.run_id == job.job_id and all(
            s.status == "skipped" for s in report.stages
        )
        state = load(scope.settings.root, "workflow_test", scope.actor)
        parsing = next(
            s for s in state.report.stages if s.process_id == "material_parsing"
        )
        assert (
            parsing.job_id == job.job_id and parsing.finished_at and parsing.started_at
        )
        names = {
            o.kind: scope.settings.root / o.path
            for o in parsing.output_refs
            if o.kind != "image"
        }
        receipt = ArtifactReceipt.model_validate_json(names["receipt"].read_bytes())
        doc = NormalizedDocument.model_validate_json(names["normalized"].read_bytes())
        assert doc.binding == receipt.binding == next(iter(prepared.bindings.values()))
        assert doc.parser == config and receipt.normalized_sha256 == sha(
            names["normalized"].read_bytes()
        )
        assert doc.raw_sha256 == sha(names["raw"].read_bytes()) and doc.images
        handoff = next(o for o in report.output_refs if o.kind == "handoff")
        data = json.loads((scope.settings.root / handoff.path).read_text())
        assert data["execution_supported"] is False
        assert (
            NormalizedDocument.model_validate(data["document"]).document_id
            == doc.document_id
        )
        assert doc.binding.lecture_ids
        assert run(scope, executor, True).job_id == job.job_id
        assert len(Controller(scope.settings).store.all()) == 1
        assert original == {
            n: (scope.entry.root / n).read_bytes() for n in scope.entry.files
        }
    finally:
        executor.close()


@pytest.mark.parametrize(
    "damage", ["raw", "normalized", "receipt", "image", "configuration"]
)
def test_pdf_stale_resume_uses_new_outputs_without_overwriting_prior_files(
    scope, damage
):
    executor = Executor(scope.settings)
    try:
        first = run(scope, executor)
        assert first.status == "completed"
    finally:
        executor.close()
    state = load(scope.settings.root, "workflow_test", scope.actor)
    stage = next(s for s in state.report.stages if s.process_id == "material_parsing")
    if damage == "configuration":
        path = scope.entry.root / "workflow.json"
        value = json.loads(path.read_text())
        value["max_blocks"] += 1
        path.write_text(json.dumps(value))
        scope.entry = scope.entry.model_copy(
            update=dict(
                files={
                    n: sha((scope.entry.root / n).read_bytes())
                    for n in scope.entry.files
                }
            )
        )
        scope.settings = scope.settings.model_copy(
            update=dict(catalog=dict(source=scope.entry))
        )
    else:
        ref = next(o for o in stage.output_refs if o.kind == damage)
        (scope.settings.root / ref.path).write_bytes(b"changed synthetic output")
    preserved = {
        o.path: (scope.settings.root / o.path).read_bytes()
        for s in state.report.stages
        for o in s.output_refs
    }
    report, _, _ = inspect(scope.settings, scope.actor, "source", "workflow_test")
    assert any(
        s.process_id == "material_parsing" and s.status == "stale"
        for s in report.stages
    )
    assert any(
        s.process_id == "lecture_material_handoff" and s.status == "stale"
        for s in report.stages
    )
    executor = Executor(scope.settings)
    try:
        resumed = run(scope, executor, True)
        assert resumed.status == "completed" and resumed.job_id != first.job_id
        assert preserved == {
            p: (scope.settings.root / p).read_bytes() for p in preserved
        }
        assert run(scope, executor, True).job_id == resumed.job_id
    finally:
        executor.close()


@pytest.mark.parametrize(
    "mode", ["cancel", "worker-timeout", "job-timeout", "executor-kill"]
)
def test_pdf_workflow_interrupted_stage_is_not_skipped_and_explicit_resume_succeeds(
    scope, mode
):
    prctl(36, 1)
    (scope.tmp / "config.json").write_text(scope.settings.model_dump_json())
    if mode.endswith("timeout"):
        (scope.tmp / mode).write_text("5" if mode == "job-timeout" else "")
    bootstrap = Executor(scope.settings)
    try:
        job = submit(scope.settings, scope.actor, "source", "workflow_test")
    finally:
        bootstrap.close()
    worker = subprocess.Popen(
        [sys.executable, str(PROBE), "executor", str(scope.tmp)],
        env=clean_environment(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    controller = Controller(scope.settings)
    try:
        marker = scope.tmp / "pdf-pid.json"
        wait_for(marker.exists)
        details = json.loads(marker.read_text())
        if mode == "cancel":
            controller.cancel(scope.actor, job.job_id)
        elif mode == "executor-kill":
            worker.kill()
            worker.wait(timeout=3)
            recovery = Executor(scope.settings)
            try:
                recovery.step()
                assert not recovery.children
            finally:
                recovery.close()
        ended = wait_for(
            lambda: (
                current
                if (current := controller.get(scope.actor, job.job_id)).status
                in TERMINAL
                else None
            )
        )
        assert ended.status == (
            "cancelled"
            if mode == "cancel"
            else "interrupted"
            if mode == "executor-kill"
            else "failed"
        )
        assert not Path(f"/proc/{details['pid']}").exists()
        state = load(scope.settings.root, "workflow_test", scope.actor)
        completed = {
            o.path: (scope.settings.root / o.path).read_bytes()
            for s in state.report.stages
            if s.status == "completed"
            for o in s.output_refs
        }
        report, _, _ = inspect(scope.settings, scope.actor, "source", "workflow_test")
        parsing = next(s for s in report.stages if s.process_id == "material_parsing")
        assert (
            parsing.status not in {"completed", "skipped"} and not parsing.output_refs
        )
        if worker.poll() is None:
            worker.kill()
            worker.wait(timeout=3)
        guardian = json.loads((scope.tmp / "guardian-pid.json").read_text())
        try:
            wait_for(lambda: os.waitpid(guardian, os.WNOHANG)[0])
        except ChildProcessError:
            pass
        restarted = Executor(scope.settings)
        try:
            restarted.step()
            assert not restarted.children
            assert (
                finish(
                    scope,
                    restarted,
                    submit(
                        scope.settings,
                        scope.actor,
                        "source",
                        "workflow_test",
                        resume=True,
                    ),
                ).status
                == "completed"
            )
            assert completed == {
                p: (scope.settings.root / p).read_bytes() for p in completed
            }
        finally:
            restarted.close()
    finally:
        if worker.poll() is None:
            worker.kill()
        worker.wait(timeout=3)
