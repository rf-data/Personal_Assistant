"""PDF-v2 approved inputs and real Linux process lifecycle, entirely offline."""

import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from scripts.job_control_demo import DEMO_TOKEN
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.guardian import REPOSITORY, clean_environment, prctl
from src.job_control.metrics import render_metrics
from src.job_control.models import TERMINAL, CatalogEntry, Identity, PdfParams, Settings
from src.job_control.pdf_adapter import PDF_CONFIG
from src.job_control.registry import registry_document
from src.job_control.store import Conflict
from src.model_materials.materials import ArtifactReceipt, NormalizedDocument
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.processing import MaterialProcessor
from tests.test_cs50_material_download import binding
from tests.test_cs50_material_pdf import pdf_bytes

PROBE = REPOSITORY / "tests/helpers/pdf_lifecycle_probe.py"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def wait_for(predicate, timeout=12):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        value = predicate()
        if value:
            return value
        time.sleep(0.02)
    pytest.fail("Bounded PDF lifecycle condition not reached")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("PDF tests forbid network access")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def pdf_scope(tmp_path):
    raw = tmp_path / "synthetic.pdf"
    raw.write_bytes(pdf_bytes())
    resource = binding("pdf", "slides").model_copy(
        update=dict(source_origin="synthetic")
    )
    workspace = tmp_path / "approved"
    receipt = MaterialDownloader(workspace).obtain(
        resource, execute=True, local_file=raw
    )
    return scope_for(tmp_path, workspace, receipt)


def scope_for(tmp_path, workspace, receipt):
    mid = receipt.binding.material_id.split(":")[1]
    entry = CatalogEntry(
        kind="pdf_bundle",
        root=workspace,
        files={
            str(p.relative_to(workspace)): sha(p.read_bytes())
            for p in workspace.rglob("*")
            if p.is_file() and p.name != ".materials.lock"
        },
        roles=dict(raw=f"{mid}/raw/source", receipt=f"{mid}/receipt.v1.json"),
        course_ids=("cs50_python",),
    )
    actor = Identity(
        subject="pdf-operator",
        role="operator",
        courses=("cs50_python",),
        token_sha256=sha(DEMO_TOKEN.encode()),
    )
    settings = Settings(
        root=tmp_path / "private",
        execution_enabled=True,
        pdf_enabled=True,
        catalog=dict(pdf=entry),
        identities=(actor,),
    )
    return SimpleNamespace(
        tmp=tmp_path,
        settings=settings,
        entry=entry,
        actor=actor,
        receipt=receipt,
        controller=Controller(settings),
    )


def create(scope, key="synthetic_pdf_request_0001", start=True):
    preview = scope.controller.preview(
        scope.actor,
        dict(
            process_id="material_parsing",
            parameters=dict(material_ref="pdf", course_id="cs50_python"),
        ),
    )
    return scope.controller.create(
        scope.actor,
        dict(preview=preview.model_dump(mode="json"), confirmed=True, start=start),
        key,
    )


def finish(scope, executor, job):
    def ended():
        executor.step()
        current = scope.controller.get(scope.actor, job.job_id)
        return current if current.status in TERMINAL else None

    return wait_for(ended, 25)


def source_bytes(scope):
    return {n: (scope.entry.root / n).read_bytes() for n in scope.entry.files}


def test_pdf_success_provenance_idempotence_and_terminal_cancel(pdf_scope):
    scope = pdf_scope
    original = source_bytes(scope)
    executor = Executor(scope.settings)
    try:
        job = create(scope)
        result = finish(scope, executor, job)
        assert result.status == "completed" and result.exit_code == 0
        assert result.started_at and result.finished_at and result.duration_seconds > 0
        assert result.artifact_refs[0].kind == "material_receipt"
        directory = scope.controller.store.directory(job.job_id) / "results"
        raw = (directory / "pdf-receipt.json").read_bytes()
        assert sha(raw) == result.artifact_refs[0].sha256
        receipt = ArtifactReceipt.model_validate_json(raw)
        doc = NormalizedDocument.model_validate_json(
            (directory / "materials" / receipt.normalized_path).read_bytes()
        )
        assert receipt.binding == scope.receipt.binding == doc.binding
        assert receipt.parser == doc.parser == PDF_CONFIG
        assert receipt.raw_sha256 == doc.raw_sha256 == scope.receipt.raw_sha256
        assert receipt.normalized_sha256 == sha(
            (directory / "materials" / receipt.normalized_path).read_bytes()
        )
        assert create(scope) == result
        with pytest.raises(Conflict):
            scope.controller.cancel(scope.actor, job.job_id)
        executor.step()
        assert len(scope.controller.store.all()) == 1
        metrics = render_metrics(scope.controller.store, 5)
        assert (
            'process="material_parsing"' in metrics and 'outcome="success"' in metrics
        )
        assert job.job_id not in metrics and str(scope.tmp) not in metrics
        assert source_bytes(scope) == original
    finally:
        executor.close()


@pytest.mark.parametrize("damage", ["missing", "hash", "receipt_hash", "invalid_pdf"])
def test_invalid_inputs_no_dispatch_or_overwrite(pdf_scope, damage):
    scope = pdf_scope
    path = scope.entry.root / scope.entry.roles["raw"]
    if damage == "missing":
        path.rename(scope.tmp / "preserved.pdf")
    elif damage in {"hash", "invalid_pdf"}:
        path.write_bytes(b"%PDF-corrupt" if damage == "invalid_pdf" else b"changed")
    else:
        target = scope.entry.root / scope.entry.roles["receipt"]
        data = json.loads(target.read_text())
        data["raw_sha256"] = "0" * 64
        target.write_text(json.dumps(data))
    if damage in {"receipt_hash", "invalid_pdf"}:
        entry = scope.entry.model_copy(
            update=dict(
                files={
                    n: sha((scope.entry.root / n).read_bytes())
                    for n in scope.entry.files
                }
            )
        )
        scope.settings = scope.settings.model_copy(update=dict(catalog=dict(pdf=entry)))
        scope.controller = Controller(scope.settings)
    if damage == "invalid_pdf":
        # Independently approve corrupt PDF bytes and their matching raw receipt.
        target = scope.entry.root / scope.entry.roles["receipt"]
        data = json.loads(target.read_text())
        data["raw_sha256"] = sha(path.read_bytes())
        target.write_text(json.dumps(data))
        entry = scope.settings.catalog["pdf"].model_copy(
            update=dict(
                files={
                    n: sha((scope.entry.root / n).read_bytes())
                    for n in scope.entry.files
                }
            )
        )
        scope.settings = scope.settings.model_copy(update=dict(catalog=dict(pdf=entry)))
        scope.controller = Controller(scope.settings)
        executor = Executor(scope.settings)
        try:
            result = finish(scope, executor, create(scope))
            assert (
                result.status == "failed"
                and result.error_class == "input"
                and result.exit_code == 2
            )
            assert not result.artifact_refs and path.read_bytes() == b"%PDF-corrupt"
        finally:
            executor.close()
    else:
        with pytest.raises((ValueError, OSError)):
            create(scope, start=False)
        assert not scope.controller.store.all()


@pytest.mark.parametrize("corrupt", [False, True])
def test_existing_output_is_validated_preserved_and_never_overwritten(
    pdf_scope, corrupt
):
    scope = pdf_scope
    receipt = MaterialProcessor(scope.entry.root).parse(
        scope.receipt.binding, execute=True, config=PDF_CONFIG
    )
    target = scope.entry.root / receipt.normalized_path
    if corrupt:
        target.write_bytes(b"invalid existing artifact")
    scope = scope_for(scope.tmp, scope.entry.root, receipt)
    original = source_bytes(scope)
    if corrupt:
        with pytest.raises((ValueError, RuntimeError)):
            create(scope, start=False)
    else:
        executor = Executor(scope.settings)
        try:
            assert finish(scope, executor, create(scope)).status == "completed"
        finally:
            executor.close()
    assert source_bytes(scope) == original


def test_opt_in_paths_versions_scope_and_revocation(pdf_scope):
    scope = pdf_scope
    assert len(registry_document()["processes"]) == 2
    assert len(registry_document(pdf=True)["processes"]) == 3
    assert "material_parsing" not in registry_document(pdf=True)["disabled_processes"]
    contract = json.loads(
        (REPOSITORY / "docs/job_control/contract.v1.json").read_text()
    )
    assert contract["optional_pdf_registry"] == registry_document(pdf=True)
    for extra in [
        dict(path="/etc/passwd"),
        dict(command="sh"),
        dict(parser_version="1"),
    ]:
        with pytest.raises(ValidationError):
            PdfParams(material_ref="pdf", course_id="cs50_python", **extra)
    disabled = scope.settings.model_copy(update=dict(pdf_enabled=False))
    with pytest.raises(PermissionError):
        Controller(disabled).preview(
            scope.actor,
            dict(
                process_id="material_parsing",
                parameters=dict(material_ref="pdf", course_id="cs50_python"),
            ),
        )
    executor = Executor(scope.settings)
    try:
        job = create(scope)
    finally:
        executor.close()
    executor = Executor(disabled)
    try:
        executor.step()
        assert scope.controller.get(scope.actor, job.job_id).status == "failed"
        assert not executor.children
    finally:
        executor.close()


def test_changed_after_confirmation_and_existing_job_directory_fail_closed(pdf_scope):
    scope = pdf_scope
    executor = Executor(scope.settings)
    try:
        job = create(scope)
        directory = scope.controller.store.directory(job.job_id)
        directory.mkdir()
        sentinel = directory / "existing-valid-output"
        sentinel.write_bytes(b"preserve this artifact")
        result = finish(scope, executor, job)
        assert result.status == "failed" and not executor.children
        assert sentinel.read_bytes() == b"preserve this artifact"
        job = create(scope, key="changed_confirmed_input_0002")
        path = scope.entry.root / scope.entry.roles["raw"]
        path.write_bytes(b"changed after confirmation")
        result = finish(scope, executor, job)
        assert result.status == "failed" and result.exit_code == 2
        assert not result.artifact_refs
        assert path.read_bytes() == b"changed after confirmation"
    finally:
        executor.close()


@pytest.mark.parametrize(
    "mode", ["cancel", "worker-timeout", "job-timeout", "executor-kill", "adapter-exit"]
)
def test_real_pdf_worker_cancel_timeouts_parent_death_and_restart(pdf_scope, mode):
    scope = pdf_scope
    original = source_bytes(scope)
    prctl(36, 1)  # Adopt our known guardian for reaping after executor SIGKILL.
    if mode.endswith("timeout"):
        (scope.tmp / mode).touch()
    (scope.tmp / "config.json").write_text(scope.settings.model_dump_json())
    job = create(scope, start=False)
    scope.controller.store.transition(
        job.job_id, "queued", "queued", "Trusted offline probe"
    )
    unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time;time.sleep(60)"], start_new_session=True
    )
    worker = subprocess.Popen(
        [sys.executable, str(PROBE), "executor", str(scope.tmp)],
        env=clean_environment(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        marker = scope.tmp / "pdf-pid.json"
        wait_for(marker.exists)
        details = json.loads(marker.read_text())
        assert details["group"] == details["parent"]  # Owned adapter is the leader.
        if mode == "cancel":
            first = scope.controller.cancel(scope.actor, job.job_id)
            assert first.status == "cancel_requested" and first.finished_at is None
            assert scope.controller.cancel(scope.actor, job.job_id) == first
        elif mode == "executor-kill":
            worker.kill()
            worker.wait(timeout=3)
            # Reconcile immediately, while the old guardian may still hold its lock.
            recovery = Executor(scope.settings)
            try:
                recovery.step()
                assert not recovery.children
            finally:
                recovery.close()
        elif mode == "adapter-exit":
            os.kill(details["parent"], signal.SIGKILL)
        result = wait_for(
            lambda: (
                current
                if (current := scope.controller.get(scope.actor, job.job_id)).status
                in TERMINAL
                else None
            )
        )
        assert result.status == (
            "cancelled"
            if mode == "cancel"
            else "interrupted"
            if mode == "executor-kill"
            else "failed"
        )
        assert result.finished_at and result.duration_seconds > 0
        if mode.endswith("timeout"):
            assert result.error_class == "timeout"
            assert result.exit_code == (
                4 if mode == "worker-timeout" else -signal.SIGTERM
            )
            assert 'error_class="timeout"' in render_metrics(scope.controller.store, 5)
        assert not Path(f"/proc/{details['pid']}").exists()
        assert not Path(f"/proc/{details['parent']}").exists()
        assert unrelated.poll() is None and source_bytes(scope) == original
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
            assert len(scope.controller.store.all()) == 1
            assert scope.controller.get(scope.actor, job.job_id) == result
        finally:
            restarted.close()
    finally:
        if worker.poll() is None:
            worker.kill()
        worker.wait(timeout=3)
        unrelated.terminate()
        unrelated.wait(timeout=3)
