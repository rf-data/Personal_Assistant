"""C20-B: serialized HTTP -> existing C18 service -> real C16/C19 PDF workers."""

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from test_cs50_workflows import finish
from test_pdf_job_control import PROBE, wait_for
from test_pdf_job_control import offline as offline
from test_pdf_workflows import scope as scope

from scripts.cs50_workflow_demo import sha
from scripts.job_control_demo import DEMO_TOKEN
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.guardian import clean_environment, prctl
from src.job_control.http import Application
from src.job_control.models import TERMINAL, Identity
from src.job_control.store import Conflict
from src.workflows import service
from src.workflows.definition import prepare
from src.workflows.engine import sealed
from src.workflows.http_models import WorkflowInspection, WorkflowSubmission
from src.workflows.state import load, save

REQUEST = dict(source_ref="source", workflow_id="workflow_test")
KEY = "synthetic_http_workflow_001"
TOKENS = dict(
    viewer="synthetic_http_viewer_token_00000000000000",
    other="synthetic_http_other_token_000000000000000",
    foreign="synthetic_http_foreign_token_0000000000000",
)


def attach(scope):
    scope.app = Application(Controller(scope.settings))


def api(scope, method, route, body=None, *, key=None, token=DEMO_TOKEN):
    if not hasattr(scope, "app"):
        attach(scope)
    status, data, mime = scope.app.request(
        method,
        route,
        {
            "Authorization": "Bearer " + token,
            **({"Idempotency-Key": key} if key else {}),
        },
        json.dumps(body).encode() if body is not None else b"",
    )
    assert mime == "application/json"
    return status, json.loads(data)


def inspect(scope):
    status, data = api(scope, "POST", "/v1/workflows/inspect", REQUEST)
    assert status == 200, data
    return data


def confirmed(preview):
    return dict(
        **REQUEST,
        preview_id=preview["preview_id"],
        current_run_id=preview["current_job"]["job_id"]
        if preview["current_job"]
        else None,
        confirmed=True,
    )


def start(scope, *, resume=False, key=KEY, body=None):
    return api(
        scope,
        "POST",
        "/v1/workflows/" + ("resume" if resume else "execute"),
        body if body is not None else confirmed(inspect(scope)),
        key=key,
    )


def job(scope, data):
    return scope.app.controller.store.get(data["run_id"])


def completed(scope):
    executor = Executor(scope.settings)
    try:
        status, data = start(scope)
        assert status == 202, data
        ended = finish(scope, executor, job(scope, data))
        assert ended.status == "completed", ended.error
        return ended
    finally:
        executor.close()


def add_identities(scope):
    scope.settings = scope.settings.model_copy(
        update=dict(
            identities=(
                scope.actor,
                *(
                    Identity(
                        subject=name,
                        role="viewer" if name in {"viewer", "foreign"} else "operator",
                        courses=("cs50x" if name == "foreign" else "cs50_python",),
                        token_sha256=sha(token.encode()),
                    )
                    for name, token in TOKENS.items()
                ),
            )
        )
    )
    attach(scope)


def test_full_stage_preview_readonly_deterministic_and_legacy_capabilities(scope):
    attach(scope)
    before_inputs = {n: (scope.entry.root / n).read_bytes() for n in scope.entry.files}
    root = scope.settings.root
    before = {
        str(p.relative_to(root)): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and p.name not in {"jobs.sqlite3-wal", "jobs.sqlite3-shm"}
    }
    first = inspect(scope)
    assert first == inspect(scope)
    parsed = WorkflowInspection.model_validate(first)
    assert parsed.workflow == sealed(parsed.workflow)
    assert len(parsed.workflow.stages) == 5
    assert parsed.workflow.stages[0].status == "ready"
    assert any(s.status == "blocked" for s in parsed.workflow.stages)
    assert parsed.current_job is None and parsed.persisted_report is None
    after = {
        str(p.relative_to(root)): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and p.name not in {"jobs.sqlite3-wal", "jobs.sqlite3-shm"}
    }
    assert before == after
    assert before_inputs == {
        n: (scope.entry.root / n).read_bytes() for n in scope.entry.files
    }
    assert scope.app.controller.store.all() == ()
    status, cap = api(scope, "GET", "/v1/workflows/capabilities")
    assert (
        status == 200
        and cap["enabled"]
        and cap["protocol"] == "personal_assistant_workflows_v1"
    )
    status, old = api(scope, "GET", "/v1/capabilities")
    assert status == 200
    assert "workflow_http" not in old and "protocol" in old
    assert old["protocol"] == "personal_assistant_jobs_v1"


def test_real_pdf_five_stages_report_and_five_verified_reuses_same_job(scope):
    first = completed(scope)
    preview = inspect(scope)
    assert all(
        s["status"] == "skipped" and s["decision"] == "verified_reuse"
        for s in preview["workflow"]["stages"]
    )
    assert all(
        s["status"] == "completed" for s in preview["persisted_report"]["stages"]
    )
    assert preview["report_artifact"] == first.artifact_refs[0].model_dump(mode="json")
    assert preview["workflow"]["run_id"] == first.job_id
    assert preview["previous_run_id"] is None and preview["history_total"] == 1
    status, original_report = api(
        scope,
        "GET",
        f"/v1/workflows/workflow_test/runs/{first.job_id}?source_ref=source",
    )
    assert status == 200 and original_report["run_id"] == first.job_id
    assert original_report["report"] == preview["persisted_report"]
    status, report = api(
        scope, "GET", "/v1/workflows/workflow_test?source_ref=source&limit=1"
    )
    assert status == 200 and report["workflow"] == preview["workflow"]
    refs = preview["workflow"]["output_refs"]
    assert {r["kind"] for r in refs} >= {
        "raw",
        "receipt",
        "normalized",
        "image",
        "quality",
        "handoff",
    }
    original = {r["path"]: (scope.settings.root / r["path"]).read_bytes() for r in refs}
    status, resumed = start(scope, resume=True, key="synthetic_http_resume_0001")
    assert status == 202 and resumed["run_id"] == first.job_id
    WorkflowSubmission.model_validate(resumed)
    assert len(scope.app.controller.store.all()) == 1
    assert original == {p: (scope.settings.root / p).read_bytes() for p in original}


def test_concurrent_submits_lost_response_refresh_and_persistent_key_conflict(scope):
    executor = Executor(scope.settings)
    try:
        body = confirmed(inspect(scope))
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: start(scope, body=body), range(2)))
        assert [s for s, _ in responses] == [202, 202], responses
        run_id = responses[0][1]["run_id"]
        assert responses[1][1]["run_id"] == run_id
        # Both HTTP and C16 objects are recreated: browser refresh/lost response.
        attach(scope)
        assert start(scope, body=body)[1]["run_id"] == run_id
        changed = {**body, "workflow_id": "another_workflow"}
        assert start(scope, body=changed)[0] == 409
        assert (
            start(scope, resume=True, body={**body, "current_run_id": run_id})[0] == 409
        )
        ended = finish(scope, executor, scope.app.controller.store.get(run_id))
        assert ended.status == "completed"
        executor.close()
        executor = None
        assert start(scope, body=body)[1]["run_id"] == run_id
        assert len(scope.app.controller.store.all()) == 1
    finally:
        if executor:
            executor.close()


def test_crash_after_c16_commit_recovers_receipt_before_revalidating_preview(
    scope, monkeypatch
):
    executor = Executor(scope.settings)
    original = service.submit

    def lost(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("synthetic response loss after durable C16 commit")

    try:
        body = confirmed(inspect(scope))
        with monkeypatch.context() as patch:
            patch.setattr(service, "submit", lost)
            assert start(scope, body=body)[0] == 500
        assert len(scope.app.controller.store.all()) == 1
        accepted = scope.app.controller.store.all()[0]
        assert finish(scope, executor, accepted).status == "completed"
        attach(scope)
        assert start(scope, body=body)[1]["run_id"] == accepted.job_id
        assert len(scope.app.controller.store.all()) == 1
    finally:
        executor.close()


def test_rejected_reuse_reservation_cannot_turn_stale_confirmation_into_acceptance(
    scope, monkeypatch
):
    completed(scope)
    body = confirmed(inspect(scope))

    def stale(*args, **kwargs):
        raise Conflict("Synthetic preview changed immediately before C18 decision")

    with monkeypatch.context() as patch:
        patch.setattr(service, "submit", stale)
        assert (
            start(scope, resume=True, body=body, key="synthetic_rejected_reuse_001")[0]
            == 409
        )
    state = load(scope.settings.root, REQUEST["workflow_id"], scope.actor)
    parsed = next(s for s in state.report.stages if s.process_id == "material_parsing")
    ref = next(o for o in parsed.output_refs if o.kind == "normalized")
    (scope.settings.root / ref.path).write_bytes(
        b"synthetic stale output after rejected confirmation"
    )
    assert (
        start(scope, resume=True, body=body, key="synthetic_rejected_reuse_001")[0]
        == 409
    )
    assert len(scope.app.controller.store.all()) == 1


@pytest.mark.parametrize("change", ["input", "configuration", "policy", "run"])
def test_changed_preview_input_config_policy_or_parent_rejected(scope, change):
    executor = Executor(scope.settings)
    try:
        body = confirmed(inspect(scope))
        if change == "input":
            name = next(iter(prepare(scope.entry).definition.sources.values()))
            (scope.entry.root / name).write_bytes(b"changed unapproved synthetic input")
        elif change == "configuration":
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
            attach(scope)
        elif change == "policy":
            scope.settings = scope.settings.model_copy(update=dict(max_queued=7))
            attach(scope)
        else:
            assert start(scope, body=body)[0] == 202
        status, data = start(scope, body=body, key="synthetic_changed_preview_001")
        assert status == 409, data
        if change != "run":
            assert not scope.app.controller.store.all()
    finally:
        executor.close()


def test_new_key_after_active_submit_returns_same_job_and_execute_never_retries(scope):
    executor = Executor(scope.settings)
    try:
        status, first = start(scope)
        assert status == 202
        status, second = start(scope, key="synthetic_active_submit_0001")
        assert status == 202 and second["run_id"] == first["run_id"]
        store = scope.app.controller.store
        store.transition(
            first["run_id"],
            "failed",
            "failed",
            "Synthetic prior failure",
            exit_code=2,
            error_class="input",
        )
        preview = inspect(scope)
        assert (
            preview["current_job"]["status"]
            == preview["workflow"]["status"]
            == "failed"
        )
        status, same = start(scope, key="synthetic_failed_execute_001")
        assert status == 202 and same["run_id"] == first["run_id"]
        assert len(store.all()) == 1
        status, resumed = start(scope, resume=True, key="synthetic_failed_resume_001")
        assert status == 202 and resumed["run_id"] != first["run_id"]
        assert job(scope, resumed).parameters["previous_run_id"] == first["run_id"]
        assert finish(scope, executor, job(scope, resumed)).status == "completed"
    finally:
        executor.close()


@pytest.mark.parametrize("damage", ["normalized", "configuration"])
def test_stale_resume_runs_only_required_stages_and_preserves_old_bytes(scope, damage):
    first = completed(scope)
    reuse_body = confirmed(inspect(scope))
    assert (
        start(scope, resume=True, body=reuse_body, key="synthetic_prior_reuse_001")[1][
            "run_id"
        ]
        == first.job_id
    )
    state = load(scope.settings.root, REQUEST["workflow_id"], scope.actor)
    parsing = next(s for s in state.report.stages if s.process_id == "material_parsing")
    if damage == "normalized":
        output = next(o for o in parsing.output_refs if o.kind == damage)
        (scope.settings.root / output.path).write_bytes(b"synthetic damaged output")
    else:
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
        attach(scope)
    old = {
        o.path: (scope.settings.root / o.path).read_bytes()
        for s in state.report.stages
        for o in s.output_refs
    }
    preview = inspect(scope)
    assert [s["status"] for s in preview["workflow"]["stages"]] == [
        "skipped",
        "skipped",
        "stale",
        "stale",
        "stale",
    ]
    executor = Executor(scope.settings)
    try:
        status, response = start(scope, resume=True, key="synthetic_stale_resume_001")
        assert status == 202 and response["run_id"] != first.job_id
        assert finish(scope, executor, job(scope, response)).status == "completed"
        report = inspect(scope)
        assert (
            report["previous_run_id"] == first.job_id and report["history_total"] == 2
        )
        stages = report["persisted_report"]["stages"]
        assert [s["status"] for s in stages] == [
            "skipped",
            "skipped",
            "completed",
            "completed",
            "completed",
        ]
        assert [s["job_id"] for s in stages[:2]] == [first.job_id, first.job_id]
        assert old == {p: (scope.settings.root / p).read_bytes() for p in old}
        assert (
            start(scope, resume=True, body=reuse_body, key="synthetic_prior_reuse_001")[
                1
            ]["run_id"]
            == first.job_id
        )
        assert len(scope.app.controller.store.all()) == 2
        status, historical = api(
            scope,
            "GET",
            f"/v1/workflows/workflow_test/runs/{first.job_id}?source_ref=source",
        )
        assert status == 200 and historical["report"] == state.report.model_dump(
            mode="json"
        )
        assert (
            start(
                scope,
                body=confirmed(preview),
                resume=True,
                key="synthetic_stale_resume_001",
            )[1]["run_id"]
            == response["run_id"]
        )
    finally:
        executor.close()


def test_roles_owner_course_flags_and_unapproved_bundle(scope):
    add_identities(scope)
    assert (
        api(scope, "POST", "/v1/workflows/inspect", REQUEST, token=TOKENS["viewer"])[0]
        == 200
    )
    body = confirmed(inspect(scope))
    for token in (TOKENS["viewer"], TOKENS["foreign"]):
        assert (
            api(scope, "POST", "/v1/workflows/execute", body, key=KEY, token=token)[0]
            == 403
        )
    assert (
        api(scope, "POST", "/v1/workflows/inspect", REQUEST, token=TOKENS["foreign"])[0]
        == 403
    )
    assert (
        api(
            scope, "POST", "/v1/workflows/inspect", {**REQUEST, "source_ref": "unknown"}
        )[0]
        == 422
    )
    assert (
        api(
            scope,
            "POST",
            "/v1/workflows/inspect",
            {**REQUEST, "source_ref": "/tmp/outside.pdf"},
        )[0]
        == 422
    )
    executor = Executor(scope.settings)
    try:
        status, response = start(scope, body=body)
        assert status == 202
        for token in (TOKENS["viewer"], TOKENS["other"]):
            assert (
                api(scope, "POST", "/v1/workflows/inspect", REQUEST, token=token)[0]
                == 403
            )
            assert (
                api(
                    scope,
                    "GET",
                    "/v1/workflows/workflow_test?source_ref=source",
                    token=token,
                )[0]
                == 403
            )
        # A viewer for the same authenticated subject may read, never execute.
        viewer = scope.actor.model_copy(update=dict(role="viewer"))
        scope.settings = scope.settings.model_copy(update=dict(identities=(viewer,)))
        attach(scope)
        assert inspect(scope)["current_job"]["job_id"] == response["run_id"]
        assert start(scope, body=body)[0] == 403
        scope.settings = scope.settings.model_copy(update=dict(workflows_enabled=False))
        attach(scope)
        assert api(scope, "POST", "/v1/workflows/inspect", REQUEST)[0] == 403
        assert api(scope, "GET", "/v1/workflows/capabilities")[1]["enabled"] is False
    finally:
        executor.close()


@pytest.mark.parametrize(
    "change", ["report_bytes", "state_hash", "foreign_reference", "unbound_output"]
)
def test_tampered_reports_references_are_rejected_before_opening_stage_paths(
    scope, change
):
    first = completed(scope)
    state = load(scope.settings.root, REQUEST["workflow_id"], scope.actor)
    if change == "report_bytes":
        path = scope.settings.root / f"jobs/{first.job_id}/results/workflow-report.json"
        path.write_bytes(b"tampered synthetic report")
    elif change == "state_hash":
        save(
            scope.settings.root,
            state.model_copy(
                update=dict(
                    report=state.report.model_copy(update=dict(report_sha256="0" * 64))
                )
            ),
        )
    else:
        stage = state.report.stages[0]
        output = stage.output_refs[0].model_copy(
            update=dict(path="jobs/foreign/results/stages/forged/private.json")
        )
        if change == "foreign_reference":
            stage = stage.model_copy(update=dict(output_refs=(output,)))
            report = sealed(
                state.report.model_copy(
                    update=dict(stages=(stage, *state.report.stages[1:]))
                )
            )
        else:
            report = sealed(state.report.model_copy(update=dict(output_refs=(output,))))
        save(scope.settings.root, state.model_copy(update=dict(report=report)))
    assert api(scope, "POST", "/v1/workflows/inspect", REQUEST)[0] == 422
    assert api(scope, "GET", "/v1/workflows/workflow_test?source_ref=source")[0] == 422


@pytest.mark.parametrize(
    "body_change",
    [
        dict(confirmed=1),
        dict(confirmed="true"),
        dict(confirmed=False),
        dict(schema_version=2),
        dict(command="sh"),
        dict(current_run_id="../outside"),
    ],
)
def test_request_schema_and_explicit_confirmation(scope, body_change):
    body = {**confirmed(inspect(scope)), **body_change}
    assert start(scope, body=body)[0] == 422
    assert scope.app.controller.store.all() == ()


def test_unknown_routes_query_bounds_and_missing_key(scope):
    # The identifier "capabilities" is a usable stable C18 workflow ID, too.
    status, named = api(scope, "GET", "/v1/workflows/capabilities?source_ref=source")
    assert status == 200 and named["workflow"]["workflow_id"] == "capabilities"
    body = confirmed(inspect(scope))
    assert start(scope, body=body, key=None)[0] == 422
    assert start(scope, resume=True, body=body)[0] == 422
    assert api(scope, "POST", "/v1/workflows/inspect?command=x", REQUEST)[0] == 422
    assert (
        api(scope, "GET", "/v1/workflows/workflow_test?source_ref=source&limit=101")[0]
        == 422
    )
    assert (
        api(
            scope,
            "GET",
            "/v1/workflows/workflow_test?source_ref=source&source_ref=source",
        )[0]
        == 422
    )
    assert api(scope, "POST", "/v1/workflows/unknown", REQUEST)[0] == 404
    assert api(scope, "GET", "/v1/workflows/workflow_test")[0] == 422
    assert (
        api(scope, "GET", "/v1/workflows/workflow_test/runs/unknown?source_ref=source")[
            0
        ]
        == 404
    )
    assert (
        api(scope, "POST", "/v1/workflows/inspect", REQUEST, token="wrong_token")[0]
        == 401
    )


def test_invalid_input_fresh_preview_blocked_bundle_and_pending_intent(scope):
    name = next(iter(prepare(scope.entry).definition.sources.values()))
    (scope.entry.root / name).write_bytes(b"changed unapproved synthetic input")
    body = confirmed(inspect(scope))
    assert start(scope, body=body)[0] == 422
    assert scope.app.controller.store.all() == ()


@pytest.mark.parametrize(
    "damage", ["missing_definition", "invalid_json", "invalid_manifest"]
)
def test_invalid_approved_bundle_is_validation_error_without_a_job(scope, damage):
    attach(scope)
    path = (
        scope.entry.root
        / scope.entry.roles["workflow" if damage != "invalid_manifest" else "manifest"]
    )
    if damage == "missing_definition":
        path.unlink()
    else:
        path.write_bytes(b"[invalid" if damage == "invalid_json" else b"{}")
    assert api(scope, "POST", "/v1/workflows/inspect", REQUEST)[0] == 422
    assert scope.app.controller.store.all() == ()


def test_pending_request_after_unavailable_worker_is_bound_and_revalidated(scope):
    body = confirmed(inspect(scope))
    assert start(scope, body=body)[0] == 503
    assert not scope.app.controller.store.all()
    assert start(scope, body={**body, "preview_id": "0" * 64})[0] == 409
    executor = Executor(scope.settings)
    try:
        assert start(scope, body=body)[0] == 202
        assert len(scope.app.controller.store.all()) == 1
    finally:
        executor.close()


def test_source_identity_is_stable_before_first_stage_and_course_revocation(scope):
    executor = Executor(scope.settings)
    try:
        status, first = start(scope)
        assert status == 202
        scope.settings = scope.settings.model_copy(
            update=dict(catalog=dict(source=scope.entry, alias=scope.entry))
        )
        attach(scope)
        assert (
            api(
                scope,
                "POST",
                "/v1/workflows/inspect",
                {**REQUEST, "source_ref": "alias"},
            )[0]
            == 409
        )
        denied = scope.actor.model_copy(update=dict(courses=("cs50x",)))
        scope.settings = scope.settings.model_copy(update=dict(identities=(denied,)))
        attach(scope)
        assert (
            api(
                scope,
                "GET",
                f"/v1/workflows/workflow_test/runs/{first['run_id']}?source_ref=source",
            )[0]
            == 403
        )
    finally:
        executor.close()


def test_versioned_schema_snapshots_and_original_c16_models(scope):
    from src.job_control.guardian import REPOSITORY
    from src.workflows import http_models

    for relative in (
        "docs/job_control/contract.v1.json",
        "docs/workflows/contract.v1.json",
    ):
        snapshot = json.loads((REPOSITORY / relative).read_text())["workflow_http"]
        assert snapshot["protocol"] == "personal_assistant_workflows_v1"
        for name, schema in snapshot["models"].items():
            assert schema == getattr(http_models, name).model_json_schema()


def test_inspect_never_calls_mutation_or_execution_helpers(scope, monkeypatch):
    import src.tools_materials.storage as storage
    import src.workflows.state as state

    attach(scope)

    def forbidden(*args, **kwargs):
        pytest.fail("Read-only workflow route attempted a mutation")

    monkeypatch.setattr(service, "submit", forbidden)
    monkeypatch.setattr(storage, "save_model", forbidden)
    monkeypatch.setattr(state, "save", forbidden)
    monkeypatch.setattr(Controller, "create", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    assert inspect(scope)["current_job"] is None
    assert api(scope, "GET", "/v1/workflows/workflow_test?source_ref=source")[0] == 200


def test_demo_no_overwrite_rejects_before_running_any_work(tmp_path, monkeypatch):
    from scripts import cs50_workflow_http_demo as demo

    path = tmp_path / "existing.json"
    path.write_bytes(b"preserve existing synthetic report")

    def forbidden(*args, **kwargs):
        pytest.fail("Demo executed before no-overwrite check")

    monkeypatch.setattr(demo, "capture", forbidden)
    with pytest.raises(SystemExit) as failure:
        demo.main(["--output", str(path)])
    assert failure.value.code == 2
    assert path.read_bytes() == b"preserve existing synthetic report"


def test_published_full_http_messages_validate_without_reinterpreting_reports():
    from src.job_control.guardian import REPOSITORY
    from src.workflows import http_models

    data = json.loads((REPOSITORY / "docs/workflows/example-http.v1.json").read_text())
    assert data["synthetic"] and data["resume_same_job"] and data["job_count"] == 1
    for message in data["messages"]:
        response = message["response"]
        if message["path"].endswith("capabilities"):
            model = http_models.WorkflowCapabilities
        elif "/runs/" in message["path"]:
            model = http_models.WorkflowRunReport
        elif message["path"].endswith(("execute", "resume")):
            model = http_models.WorkflowSubmission
        else:
            model = http_models.WorkflowInspection
        model.model_validate(response)
    statuses = [
        m["response"]
        for m in data["messages"]
        if m["method"] == "GET"
        and "?source_ref=" in m["path"]
        and "/runs/" not in m["path"]
    ]
    assert len(statuses) == 1
    assert all(
        s["status"] == "skipped" and s["decision"] == "verified_reuse"
        for s in statuses[0]["workflow"]["stages"]
    )


@pytest.mark.parametrize("mode", ["cancel", "worker-timeout", "executor-kill"])
def test_http_pdf_cancel_timeout_restart_and_explicit_resume(scope, mode):
    prctl(36, 1)
    (scope.tmp / "config.json").write_text(scope.settings.model_dump_json())
    if mode == "worker-timeout":
        (scope.tmp / mode).write_text("")
    bootstrap = Executor(scope.settings)
    try:
        status, response = start(scope)
        assert status == 202
    finally:
        bootstrap.close()
    worker = subprocess.Popen(
        [sys.executable, str(PROBE), "executor", str(scope.tmp)],
        env=clean_environment(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        wait_for((scope.tmp / "pdf-pid.json").exists)
        live = inspect(scope)
        assert live["current_job"]["status"] == "running"
        assert any(s["status"] == "running" for s in live["workflow"]["stages"])
        if mode == "cancel":
            status, cancelling = api(
                scope, "POST", f"/v1/jobs/{response['run_id']}/cancel", {}
            )
            assert status == 202 and cancelling["status"] == "cancel_requested"
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
                if (current := job(scope, response)).status in TERMINAL
                else None
            )
        )
        assert ended.status == (
            "cancelled"
            if mode == "cancel"
            else "failed"
            if mode == "worker-timeout"
            else "interrupted"
        )
        if mode == "worker-timeout":
            assert ended.error_class == "timeout"
        report = inspect(scope)
        parsing = next(
            s
            for s in report["workflow"]["stages"]
            if s["process_id"] == "material_parsing"
        )
        assert parsing["status"] not in {"skipped", "completed"}
        state = load(scope.settings.root, REQUEST["workflow_id"], scope.actor)
        preserved = {
            o.path: (scope.settings.root / o.path).read_bytes()
            for s in state.report.stages
            if s.status == "completed"
            for o in s.output_refs
        }
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
            status, resumed = start(
                scope, resume=True, key="synthetic_lifecycle_resume_001"
            )
            assert status == 202 and resumed["run_id"] != response["run_id"]
            assert finish(scope, restarted, job(scope, resumed)).status == "completed"
            assert preserved == {
                p: (scope.settings.root / p).read_bytes() for p in preserved
            }
        finally:
            restarted.close()
    finally:
        if worker.poll() is None:
            worker.kill()
        worker.wait(timeout=3)
