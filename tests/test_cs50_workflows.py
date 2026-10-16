"""Isolated offline graph, provenance, resume and real C16 workflow tests."""

import json
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from scripts.cs50_workflow import main
from scripts.cs50_workflow_demo import inputs, sha
from scripts.job_control_demo import DEMO_TOKEN
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.models import TERMINAL, Identity, Settings
from src.job_control.store import Unavailable
from src.workflows.definition import DEFERRED, prepare
from src.workflows.engine import preview, sealed
from src.workflows.graph import topological
from src.workflows.models import VALID, State
from src.workflows.service import inspect, jobs, submit
from src.workflows.state import directory, load, save


def wait_for_commit(scope, step=lambda: None):
    until = time.monotonic() + 15
    while time.monotonic() < until:
        step()
        state = load(scope.settings.root, "workflow_test", scope.actor)
        if state and any(s.status == "completed" for s in state.report.stages):
            return state
        time.sleep(0.005)
    pytest.fail("No stage commit within test bound")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Workflow network access forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def scope(tmp_path):
    entry = inputs(tmp_path / "inputs")
    settings = Settings(
        root=tmp_path / "private",
        catalog=dict(source=entry),
        workflows_enabled=True,
        execution_enabled=True,
        identities=(
            Identity(
                subject="operator",
                role="operator",
                courses=("cs50_python",),
                token_sha256=sha(DEMO_TOKEN.encode()),
            ),
        ),
    )
    return SimpleNamespace(
        settings=settings, actor=settings.identities[0], entry=entry, tmp=tmp_path
    )


def finish(scope, executor, job):
    controller = Controller(scope.settings)
    until = time.monotonic() + 30
    while controller.get(scope.actor, job.job_id).status not in TERMINAL:
        assert time.monotonic() < until
        executor.step()
        time.sleep(0.02)
    return controller.get(scope.actor, job.job_id)


def run(scope, executor, resume=False):
    return finish(
        scope,
        executor,
        submit(scope.settings, scope.actor, "source", "workflow_test", resume=resume),
    )


def changed(scope, *, config=None, raw=None):
    path = scope.entry.root / "workflow.json"
    value = json.loads(path.read_text())
    if config:
        value.update(config)
        path.write_text(json.dumps(value))
    if raw is not None:
        name = next(
            n
            for n in value["sources"].values()
            if (scope.entry.root / n).read_bytes().startswith(b"<html")
        )
        (scope.entry.root / name).write_bytes(raw)
    scope.entry = scope.entry.model_copy(
        update=dict(
            files={
                n: sha((scope.entry.root / n).read_bytes()) for n in scope.entry.files
            }
        )
    )
    scope.settings = scope.settings.model_copy(
        update=dict(catalog={"source": scope.entry})
    )


def test_readonly_preview_deterministic_order_and_deferred_contracts(scope):
    before = {n: (scope.entry.root / n).read_bytes() for n in scope.entry.files}
    a, prepared, _ = inspect(scope.settings, scope.actor, "source", "workflow_test")
    b, _, _ = inspect(scope.settings, scope.actor, "source", "workflow_test")
    assert a == b and a.report_sha256 == b.report_sha256 and a.run_id is None
    assert len(a.stages) == 9 and a.stages[0].process_id == "material_planning"
    assert a.stages[0].status == "ready" and any(
        s.status == "blocked" for s in a.stages
    )
    assert topological(tuple(reversed(prepared.stages))) == prepared.stages
    assert not scope.settings.root.exists()
    assert before == {n: (scope.entry.root / n).read_bytes() for n in scope.entry.files}
    assert len(DEFERRED) == 5 and "knowledge_extraction" in DEFERRED


def test_graph_rejects_cycles_unknown_stages_and_duplicate_edges(scope):
    first, second = prepare(scope.entry).stages[:2]
    invalid = [
        (first, first),
        (first.model_copy(update=dict(dependencies=("unknown",))),),
        (first.model_copy(update=dict(dependencies=(second.stage_id,))), second),
        (
            first,
            second.model_copy(
                update=dict(dependencies=(first.stage_id, first.stage_id))
            ),
        ),
    ]
    for stages in invalid:
        with pytest.raises(ValueError):
            topological(stages)
    prepared = replace(
        prepare(scope.entry),
        stages=(first.model_copy(update=dict(process_id="shell_command")),),
    )
    with pytest.raises(ValueError):
        preview(prepared, scope.settings.root, "wf", "source", scope.actor)


@pytest.mark.parametrize("corrupt", [False, True])
def test_missing_and_hash_invalid_sources_block_dispatch(scope, corrupt):
    name = next(iter(prepare(scope.entry).definition.sources.values()))
    path = scope.entry.root / name
    if corrupt:
        path.write_bytes(b"changed without approval")
    else:
        path.rename(scope.tmp / "preserved_original")
    report, _, _ = inspect(scope.settings, scope.actor, "source", "workflow_test")
    assert any(name in s.missing_inputs for s in report.stages)
    with pytest.raises(ValueError):
        submit(scope.settings, scope.actor, "source", "workflow_test")
    assert not scope.settings.root.exists()


def test_real_workflow_valid_skip_provenance_and_unique_references(scope):
    before = {n: (scope.entry.root / n).read_bytes() for n in scope.entry.files}
    executor = Executor(scope.settings)
    try:
        job = run(scope, executor)
        assert job.status == "completed" and job.exit_code == 0
        report, _, _ = inspect(scope.settings, scope.actor, "source", "workflow_test")
        assert report.status == "completed" and all(
            s.status == "skipped" for s in report.stages
        )
        assert report.run_id == job.job_id and report.started_at and report.finished_at
        assert all(
            s.job_id == job.job_id and s.duration_seconds >= 0 for s in report.stages
        )
        assert len({(o.kind, o.identity, o.sha256) for o in report.output_refs}) == len(
            report.output_refs
        )
        for ref in report.output_refs:
            assert sha((scope.settings.root / ref.path).read_bytes()) == ref.sha256
        handoffs = [o for o in report.output_refs if o.kind == "handoff"]
        assert len(handoffs) == 2
        for ref in handoffs:
            data = json.loads((scope.settings.root / ref.path).read_text())
            assert data["execution_supported"] is False
            assert len(
                {u["block"]["block_id"] for u in data["aggregation_units"]}
            ) == len(data["aggregation_units"])
        assert (
            submit(
                scope.settings, scope.actor, "source", "workflow_test", resume=True
            ).job_id
            == job.job_id
        )
        assert len(jobs(scope.settings)) == 1
        assert (
            inspect(scope.settings, scope.actor, "source", "workflow_test")[0] == report
        )
        assert before == {
            n: (scope.entry.root / n).read_bytes() for n in scope.entry.files
        }
    finally:
        executor.close()


@pytest.mark.parametrize(
    "change", ["input", "config", "output", "schema", "parser", "provenance"]
)
def test_stale_propagates_and_resume_preserves_existing_outputs(scope, change):
    executor = Executor(scope.settings)
    try:
        original = run(scope, executor)
        assert original.status == "completed"
    finally:
        executor.close()
    state = load(scope.settings.root, "workflow_test", scope.actor)
    original_files = {
        o.path: (scope.settings.root / o.path).read_bytes()
        for s in state.report.stages
        for o in s.output_refs
    }
    if change == "input":
        changed(
            scope,
            raw=b"<html><main><h1>Changed notes</h1><p>New data.</p></main></html>",
        )
    elif change == "config":
        changed(scope, config=dict(max_blocks=1100))
    else:
        stage = next(
            s for s in state.report.stages if s.process_id == "material_parsing"
        )
        target = next(o for o in stage.output_refs if o.kind == "normalized")
        path = scope.settings.root / target.path
        if change == "output":
            path.write_bytes(b"corrupt")
        else:
            data = json.loads(path.read_text())
            if change == "schema":
                data["schema_version"] = 99
            elif change == "parser":
                data["parser"]["version"] = "1"
            else:
                data["raw_sha256"] = "0" * 64
            path.write_text(json.dumps(data))
            refs = tuple(
                o.model_copy(
                    update=dict(
                        sha256=sha(path.read_bytes()), size_bytes=path.stat().st_size
                    )
                )
                if o == target
                else o
                for o in stage.output_refs
            )
            stages = tuple(
                s.model_copy(update=dict(output_refs=refs))
                if s.stage_id == stage.stage_id
                else s
                for s in state.report.stages
            )
            save(
                scope.settings.root,
                State(
                    report=sealed(state.report.model_copy(update=dict(stages=stages))),
                    attempts=state.attempts,
                ),
            )
    previewed, _, _ = inspect(scope.settings, scope.actor, "source", "workflow_test")
    assert any(s.status == "stale" for s in previewed.stages)
    assert any(
        s.process_id == "lecture_material_handoff" and s.status == "stale"
        for s in previewed.stages
    )
    untouched = {
        p: b
        for p, b in original_files.items()
        if (scope.settings.root / p).read_bytes() == b
    }
    executor = Executor(scope.settings)
    try:
        resumed = run(scope, executor, True)
        assert resumed.job_id != original.job_id and resumed.status == "completed"
        assert all(
            (scope.settings.root / p).read_bytes() == b for p, b in untouched.items()
        )
        assert (
            directory(scope.settings.root, "workflow_test")
            / "history"
            / (original.job_id + ".json")
        ).exists()
    finally:
        executor.close()


@pytest.mark.parametrize("continue_independent", [True, False])
def test_partial_failure_and_independent_branch_strategy(scope, continue_independent):
    changed(scope, config=dict(continue_independent=continue_independent), raw=b"")
    executor = Executor(scope.settings)
    try:
        job = run(scope, executor)
        assert job.status == "failed" and job.exit_code == 1 and job.artifact_refs
        state = load(scope.settings.root, "workflow_test", scope.actor)
        failed = {s.stage_id for s in state.report.stages if s.status == "failed"}
        assert failed and any(s.status == "blocked" for s in state.report.stages)
        for stage in state.report.stages:
            if failed.intersection(stage.dependencies):
                assert stage.status == "blocked"
        if continue_independent:
            assert (
                sum(
                    s.process_id == "lecture_material_handoff"
                    and s.status == "completed"
                    for s in state.report.stages
                )
                == 1
            )
        else:
            assert not any(
                s.process_id == "lecture_material_handoff" and s.status == "completed"
                for s in state.report.stages
            )
    finally:
        executor.close()


def test_parallel_submission_uses_existing_queue_and_one_job(scope):
    with pytest.raises(Unavailable):
        submit(scope.settings, scope.actor, "source", "workflow_test")
    executor = Executor(scope.settings)
    try:
        with ThreadPoolExecutor(4) as pool:
            created = list(
                pool.map(
                    lambda _: submit(
                        scope.settings, scope.actor, "source", "workflow_test"
                    ),
                    range(4),
                )
            )
        assert len({j.job_id for j in created}) == 1 and len(jobs(scope.settings)) == 1
        assert finish(scope, executor, created[0]).status == "completed"
    finally:
        executor.close()


def test_queued_cancel_and_explicit_resume(scope):
    executor = Executor(scope.settings)
    try:
        job = submit(scope.settings, scope.actor, "source", "workflow_test")
        controller = Controller(scope.settings)
        assert controller.cancel(scope.actor, job.job_id).status == "cancel_requested"
        executor.step()
        assert controller.get(scope.actor, job.job_id).status == "cancelled"
        assert run(scope, executor, True).status == "completed"
    finally:
        executor.close()


def test_resume_after_interrupted_attempt_before_state_write(scope):
    executor = Executor(scope.settings)
    try:
        original = run(scope, executor)
        state = load(scope.settings.root, "workflow_test", scope.actor)
        stages = tuple(
            s.model_copy(update=dict(status="running", output_refs=()))
            if s.process_id == "material_parsing"
            else s
            for s in state.report.stages
        )
        save(
            scope.settings.root,
            State(
                report=sealed(
                    state.report.model_copy(
                        update=dict(stages=stages, status="running")
                    )
                ),
                attempts=state.attempts,
            ),
        )
        controller = Controller(scope.settings)
        p = controller.preview(
            scope.actor,
            dict(
                process_id="cs50_offline_workflow",
                parameters=dict(
                    source_ref="source",
                    course_id="cs50_python",
                    workflow_id="workflow_test",
                    previous_run_id=original.job_id,
                ),
            ),
        )
        failed = controller.create(
            scope.actor,
            dict(preview=p.model_dump(mode="json"), confirmed=True),
            "synthetic_bootstrap_failure_01",
        )
        controller.store.transition(
            failed.job_id,
            "interrupted",
            "interrupted",
            "Synthetic bootstrap interruption",
        )
        assert run(scope, executor, True).status == "completed"
    finally:
        executor.close()


def test_permissions_default_disabled_and_invalid_refs(scope):
    controller = Controller(
        scope.settings.model_copy(update=dict(workflows_enabled=False))
    )
    with pytest.raises(PermissionError):
        controller.preview(
            scope.actor,
            dict(
                process_id="cs50_offline_workflow",
                parameters=dict(
                    source_ref="source", course_id="cs50_python", workflow_id="wf"
                ),
            ),
        )
    with pytest.raises(PermissionError):
        submit(
            scope.settings,
            scope.actor.model_copy(update=dict(role="viewer")),
            "source",
            "wf",
        )
    with pytest.raises(ValueError):
        inspect(scope.settings, scope.actor, "unapproved", "wf")
    with pytest.raises(ValueError):
        inspect(scope.settings, scope.actor, "source", "../wf")
    with pytest.raises(ValidationError):
        prepare(scope.entry).definition.model_validate(dict(schema_version=2))


def test_cli_report_exports_deterministic_no_overwrite(scope, capsys):
    config = scope.tmp / "config.json"
    config.write_text(scope.settings.model_dump_json())
    token = scope.tmp / "token"
    token.write_text(DEMO_TOKEN)
    target = scope.tmp / "report.json"
    md = scope.tmp / "report.md"
    base = [
        "--config",
        str(config),
        "--token-file",
        str(token),
        "--source-ref",
        "source",
    ]
    assert (
        main(
            [
                "preview",
                *base,
                "--json-output",
                str(target),
                "--markdown-output",
                str(md),
            ]
        )
        == 0
    )
    data = target.read_bytes()
    assert json.loads(data)["schema_version"] == 1 and "# Workflow " in md.read_text()
    with pytest.raises(ValueError):
        main(["preview", *base, "--json-output", str(target)])
    assert data == target.read_bytes()
    with pytest.raises(ValueError):
        main(["execute", *base])
    assert "report_sha256" in capsys.readouterr().out


def test_cancel_during_real_execution_and_resume(scope):
    changed(
        scope,
        config=dict(max_blocks=2000),
        raw=b"<html><main><h1>Synthetic bounded fixture</h1>"
        + b"<p>A bounded offline material paragraph.</p>" * 200
        + b"</main></html>",
    )
    executor = Executor(scope.settings)
    try:
        job = submit(scope.settings, scope.actor, "source", "workflow_test")
        before = wait_for_commit(scope, executor.step)
        controller = Controller(scope.settings)
        assert controller.cancel(scope.actor, job.job_id).status == "cancel_requested"
        assert finish(scope, executor, job).status == "cancelled"
        assert (
            inspect(scope.settings, scope.actor, "source", "workflow_test")[0].status
            == "cancelled"
        )
        retained = {
            o.path: (scope.settings.root / o.path).read_bytes()
            for s in before.report.stages
            if s.status in VALID
            for o in s.output_refs
        }
        assert run(scope, executor, True).status == "completed"
        assert all(
            (scope.settings.root / p).read_bytes() == raw for p, raw in retained.items()
        )
    finally:
        executor.close()


def test_hard_worker_restart_reconciles_real_partial_workflow(scope):
    changed(
        scope,
        config=dict(max_blocks=2000),
        raw=b"<html><main><h1>Synthetic fixture</h1>"
        + b"<p>Offline data.</p>" * 200
        + b"</main></html>",
    )
    config = scope.tmp / "worker_config.json"
    config.write_text(scope.settings.model_dump_json())
    controller = Controller(scope.settings)
    worker = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "scripts.job_control",
            "worker",
            "--config",
            str(config),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        until = time.monotonic() + 10
        while not controller.store.worker_available(5):
            assert worker.poll() is None and time.monotonic() < until
            time.sleep(0.02)
        original = submit(scope.settings, scope.actor, "source", "workflow_test")
        wait_for_commit(scope)
        worker.kill()  # Direct owned unreaped synthetic test child only.
        worker.wait(timeout=10)
        executor = Executor(scope.settings)
        try:
            assert controller.get(scope.actor, original.job_id).status == "interrupted"
            report, _, _ = inspect(
                scope.settings, scope.actor, "source", "workflow_test"
            )
            assert report.status == "interrupted"
            assert any(s.status == "completed" for s in report.stages)
            assert any(s.status not in VALID for s in report.stages)
            assert all(s.status != "running" for s in report.stages)
            assert run(scope, executor, True).status == "completed"
        finally:
            executor.close()
    finally:
        if worker.poll() is None:
            worker.terminate()
            worker.wait(timeout=10)


def test_metadata_permission_and_hash_tamper_are_rejected(scope):
    executor = Executor(scope.settings)
    try:
        assert run(scope, executor).status == "completed"
    finally:
        executor.close()
    # The direct C16 adapter must enforce the same source identity as the CLI.
    from src.workflows.engine import run as run_engine

    controller = Controller(scope.settings)
    existing = jobs(scope.settings)[0]
    with pytest.raises(ValueError, match="source reference changed"):
        run_engine(
            controller.store,
            existing.model_copy(update=dict(input_refs=("other_source",))),
            prepare(scope.entry),
            scope.actor,
        )
    foreign = scope.actor.model_copy(update=dict(subject="foreign_owner"))
    with pytest.raises(PermissionError):
        load(scope.settings.root, "workflow_test", foreign)
    path = directory(scope.settings.root, "workflow_test") / "state.v1.json"
    data = json.loads(path.read_text())
    data["report"]["configuration_hash"] = "0" * 64
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load(scope.settings.root, "workflow_test", scope.actor)


def test_new_process_metrics_and_opt_in_registry(scope):
    from src.core.pipeline_metrics import Sample, validate_samples
    from src.job_control.metrics import render_metrics
    from src.job_control.registry import registry_document

    assert len(registry_document()["processes"]) == 2
    assert len(registry_document(workflows=True)["processes"]) == 3
    executor = Executor(scope.settings)
    try:
        assert run(scope, executor).status == "completed"
        metrics = render_metrics(Controller(scope.settings).store, 5)
        assert 'process="cs50_offline_workflow"' in metrics
        validate_samples(
            [
                Sample(
                    "personal_assistant_jobs_running",
                    0,
                    dict(process="cs50_offline_workflow", worker_pool="default"),
                )
            ]
        )
    finally:
        executor.close()


def test_unreviewed_pdf_version_stays_blocked_in_preview(scope, monkeypatch):
    from src.model_materials.materials import ParserConfig

    monkeypatch.setattr(
        "src.workflows.definition.parser_for",
        lambda binding: (ParserConfig(name="pdf", version="1"), "unsupported", None),
    )
    prepared = prepare(scope.entry)
    report = preview(
        prepared, scope.settings.root, "workflow_test", "source", scope.actor
    )
    parsing = [s for s in report.stages if s.process_id == "material_parsing"]
    assert parsing and all(
        s.status == "blocked" and "unsupported_parser_lifecycle" in s.missing_inputs
        for s in parsing
    )
    assert all(config is None for config in prepared.parsers.values())
    assert not scope.settings.root.exists()


def test_c16_timeout_before_workflow_state_is_reported_and_resumable(scope):
    executor = Executor(scope.settings)
    try:
        job = submit(scope.settings, scope.actor, "source", "workflow_test")
        controller = Controller(scope.settings)
        controller.store.transition(
            job.job_id, "running", "dispatching", "Synthetic preflight timeout"
        )
        controller.store.transition(
            job.job_id,
            "failed",
            "failed",
            "Synthetic timeout",
            exit_code=-9,
            error_class="timeout",
            error="Bounded synthetic timeout",
        )
        report, _, _ = inspect(scope.settings, scope.actor, "source", "workflow_test")
        assert report.status == "failed" and report.run_id == job.job_id
        assert report.errors == ("C16:failed:-9:timeout",)
        assert not any(s.status in VALID for s in report.stages)
        assert run(scope, executor, True).status == "completed"
    finally:
        executor.close()
