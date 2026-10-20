"""Offline API and real bounded adapter tests, using exclusively new fixtures."""

import hashlib
import io
import json
import re
import socket
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from scripts.job_control_demo import DEMO_TOKEN, build_inputs
from src.job_control.catalog import safe_path
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.http import Application, encode, handler_for
from src.job_control.models import TERMINAL, Identity, Settings
from src.job_control.registry import REGISTRY, registry_document
from src.job_control.store import Conflict, Store, Unavailable


def assert_metrics_contract(body):
    reference = json.loads(
        (
            Path(__file__).parent / "fixtures/job_control/c15-metrics-reference.v1.json"
        ).read_text()
    )["contract"]
    registry = {metric["name"]: metric for metric in reference["metrics"]}
    samples = [line for line in body.splitlines() if line and not line.startswith("#")]
    assert len(samples) <= reference["max_samples_per_scrape"]
    for line in samples:
        name, text, _value = re.fullmatch(r"([a-z_]+)\{([^}]+)\} (.+)", line).groups()
        labels = dict(re.findall(r'([a-z_]+)="([^"]+)"', text))
        if name == "personal_assistant_queue_jobs":
            assert set(labels) == {"process", "worker_pool"}
            continue
        family = name
        if name not in registry:
            for suffix in ("_bucket", "_count", "_sum"):
                if name.endswith(suffix):
                    family = name[: -len(suffix)]
                    break
        assert family in registry
        assert set(labels) == set(registry[family]["labels"]) | (
            {"le"} if name.endswith("_bucket") else set()
        )
        for key, value in labels.items():
            if key != "le":
                assert value in reference["labels"][key]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail("Job-control tests must remain offline")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def setup(tmp_path):
    token = DEMO_TOKEN
    identities = tuple(
        Identity(
            subject=name,
            role=role,
            courses=(course,),
            token_sha256=hashlib.sha256(value.encode()).hexdigest(),
        )
        for name, role, course, value in (
            ("operator", "operator", "cs50_python", token),
            (
                "viewer",
                "viewer",
                "cs50_python",
                "synthetic_viewer_token_000000000000000000",
            ),
            (
                "other",
                "operator",
                "cs50_python",
                "synthetic_other_token_0000000000000000000",
            ),
            ("foreign", "viewer", "cs50x", "synthetic_foreign_token_00000000000000000"),
        )
    )
    settings = Settings(
        root=tmp_path / "private",
        catalog=build_inputs(tmp_path),
        execution_enabled=True,
        identities=identities,
    )
    controller = Controller(settings)
    actor = controller.authenticate("Bearer " + token)
    return SimpleNamespace(
        settings=settings,
        controller=controller,
        actor=actor,
        app=Application(controller),
        tmp=tmp_path,
    )


def request_data(setup, process="material_planning"):
    params = (
        dict(source_ref="demo_snapshots", course_id="cs50_python", section="0")
        if process == "material_planning"
        else dict(material_ref="demo_material", course_id="cs50_python")
    )
    preview = setup.controller.preview(
        setup.actor, dict(process_id=process, parameters=params)
    )
    return dict(preview=preview.model_dump(mode="json"), confirmed=True)


def create(
    setup, key="synthetic_request_key_0001", process="material_planning", start=True
):
    return setup.controller.create(
        setup.actor, {**request_data(setup, process), "start": start}, key
    )


def finish(setup, executor, job, timeout=10):
    until = time.monotonic() + timeout
    while setup.controller.get(setup.actor, job.job_id).status not in TERMINAL:
        executor.step()
        if time.monotonic() > until:
            pytest.fail("Bounded adapter failed to finish")
        time.sleep(0.03)
    return setup.controller.get(setup.actor, job.job_id)


def api(setup, method, path, body=None, headers=None):
    auth = {"Authorization": "Bearer " + DEMO_TOKEN, **(headers or {})}
    status, raw, mime = setup.app.request(
        method, path, auth, json.dumps(body).encode() if body is not None else b""
    )
    return status, json.loads(raw) if mime == "application/json" else raw.decode()


def test_registry_and_preview_do_not_execute(setup):
    assert set(REGISTRY) == {"material_planning", "quality_evaluation"}
    doc = registry_document()
    assert "material_download" in doc["disabled_processes"]
    assert all(
        p["parameter_schema"]["additionalProperties"] is False for p in doc["processes"]
    )
    body = request_data(setup)
    assert body["preview"]["input_refs"] == ["demo_snapshots"]
    assert setup.controller.store.all() == ()
    assert not list((setup.settings.root / "jobs").iterdir())


def test_http_preview_create_never_calls_planning_runner(setup, monkeypatch):
    import src.tools_materials.processing as processing

    def forbidden(*args, **kwargs):
        pytest.fail("Planning runner executed inside the HTTP request lifecycle")

    monkeypatch.setattr(processing, "make_plan", forbidden)
    body = request_data(setup)
    job = setup.controller.create(
        setup.actor, {**body, "start": False}, "preview_without_runner_00"
    )
    assert (
        job.status == "created"
        and not setup.controller.store.directory(job.job_id).exists()
    )


@pytest.mark.parametrize("process", ["material_planning", "quality_evaluation"])
def test_real_adapters_persistence_artifacts_and_read_only_inputs(setup, process):
    before = {
        p: p.read_bytes()
        for e in setup.settings.catalog.values()
        for p in (e.root / name for name in e.files)
    }
    executor = Executor(setup.settings)
    try:
        job = create(setup, process=process)
        assert job.status == "queued" and job.progress is None
        job = finish(setup, executor, job)
        assert job.status == "completed" and job.exit_code == 0 and job.progress is None
        assert job.started_at and job.finished_at and job.duration_seconds > 0
        assert len(job.artifact_refs) == 1
        artifact = job.artifact_refs[0]
        result = (
            setup.controller.store.directory(job.job_id)
            / "results"
            / (job.parameters["output_name"] + ".json")
        )
        assert artifact.sha256 == hashlib.sha256(result.read_bytes()).hexdigest()
        assert artifact.size_bytes == result.stat().st_size
        restarted = Controller(setup.settings)
        assert restarted.get(setup.actor, job.job_id) == job
        assert len(restarted.store.all()) == 1
        assert all(p.read_bytes() == data for p, data in before.items())
        assert api(setup, "GET", "/v1/jobs/" + job.job_id + "/artifacts")[0] == 200
        metrics = api(setup, "GET", "/v1/metrics")[1]
        assert (
            'outcome="success"' in metrics and "job_duration_seconds_bucket" in metrics
        )
        assert job.job_id not in metrics and setup.actor.subject not in metrics
        assert_metrics_contract(metrics)
    finally:
        executor.close()


@pytest.mark.parametrize(
    "process",
    [
        "material_download",
        "knowledge_extraction",
        "python",
        "../../script",
        "visual_enrichment",
    ],
)
def test_process_allowlist(setup, process):
    status, data = api(
        setup, "POST", "/v1/previews", dict(process_id=process, parameters={})
    )
    assert status == 422 and data["error"]["code"] == "invalid_request"


@pytest.mark.parametrize(
    "change",
    [
        dict(output_name="../escape"),
        dict(source_ref="/etc/passwd"),
        dict(command="echo secret"),
        dict(section="/tmp"),
        dict(course_id="arbitrary"),
        dict(resource_id="not-present"),
    ],
)
def test_parameters_and_traversal(setup, change):
    params = dict(
        source_ref="demo_snapshots", course_id="cs50_python", section="0", **{}
    )
    params.update(change)
    assert (
        api(
            setup,
            "POST",
            "/v1/previews",
            dict(process_id="material_planning", parameters=params),
        )[0]
        == 422
    )
    with pytest.raises(ValueError):
        setup.controller.store.directory("../../other")


def test_missing_worker_inputs_and_closed_default(setup):
    body = request_data(setup)
    with pytest.raises(Unavailable):
        setup.controller.create(setup.actor, body, "no_worker_request_0001")
    disabled = Controller(
        setup.settings.model_copy(update={"execution_enabled": False})
    )
    with pytest.raises(Unavailable):
        disabled.create(setup.actor, body, "disabled_request_000001")
    entry = setup.settings.catalog["demo_snapshots"]
    (entry.root / entry.roles["manifest"]).unlink()
    assert (
        api(
            setup,
            "POST",
            "/v1/previews",
            dict(
                process_id="material_planning", parameters=body["preview"]["parameters"]
            ),
        )[0]
        == 503
    )


def test_confirmation_preview_tamper_and_idempotency_conflict(setup):
    executor = Executor(setup.settings)
    try:
        body = request_data(setup)
        with pytest.raises(ValidationError):
            setup.controller.create(
                setup.actor, {**body, "confirmed": False}, "bad_confirm_request_00"
            )
        bad = json.loads(json.dumps(body))
        bad["preview"]["preview_id"] = "0" * 64
        with pytest.raises(Conflict):
            setup.controller.create(setup.actor, bad, "bad_preview_request_00")
        job = setup.controller.create(setup.actor, body, "idempotency_request_00")
        assert (
            setup.controller.create(setup.actor, body, "idempotency_request_00") == job
        )
        with pytest.raises(Conflict):
            setup.controller.create(
                setup.actor, {**body, "start": False}, "idempotency_request_00"
            )
        executor.store.heartbeat(0)
        assert (
            Controller(setup.settings).create(
                setup.actor, body, "idempotency_request_00"
            )
            == job
        )
    finally:
        executor.close()


def test_parallel_requests_make_one_job(setup):
    executor = Executor(setup.settings)
    body = request_data(setup)
    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            jobs = list(
                pool.map(
                    lambda _: setup.controller.create(
                        setup.actor, body, "parallel_request_0000"
                    ),
                    range(16),
                )
            )
        assert len({j.job_id for j in jobs}) == 1
        assert len(setup.controller.store.all()) == 1
    finally:
        executor.close()


def test_roles_owners_and_all_reads_authenticated(setup):
    job = create(setup, start=False)
    for path in (
        "/v1/processes",
        "/v1/jobs",
        "/v1/jobs/" + job.job_id,
        "/v1/jobs/" + job.job_id + "/logs",
        "/v1/jobs/" + job.job_id + "/artifacts",
        "/v1/metrics",
    ):
        status, *_ = setup.app.request("GET", path, {})
        assert status == 401
    viewer = setup.settings.identities[1]
    with pytest.raises(PermissionError):
        setup.controller.create(viewer, request_data(setup), "viewer_request_000000")
    assert setup.controller.get(viewer, job.job_id) == job
    for actor in setup.settings.identities[2:]:
        with pytest.raises(PermissionError):
            setup.controller.start(actor, job.job_id)
    assert (
        setup.app.request("GET", "/v1/jobs", {"Authorization": "Bearer bad"})[0] == 401
    )


def test_queue_cancel_confirmed_only_by_executor(setup):
    executor = Executor(setup.settings)
    try:
        job = create(setup)
        requested = setup.controller.cancel(setup.actor, job.job_id)
        assert requested.status == "cancel_requested" and requested.finished_at is None
        executor.step()
        cancelled = setup.controller.get(setup.actor, job.job_id)
        assert cancelled.status == "cancelled" and cancelled.finished_at
        assert not setup.controller.store.directory(job.job_id).exists()
        with pytest.raises(Conflict):
            setup.controller.cancel(setup.actor, job.job_id)
    finally:
        executor.close()


def test_capacity_and_workspace_conflict(setup):
    settings = setup.settings.model_copy(update={"max_jobs": 1})
    setup.controller = Controller(settings)
    executor = Executor(settings)
    try:
        job = create(setup)
        directory = setup.controller.store.directory(job.job_id)
        directory.mkdir()
        (directory / "keep.txt").write_text("existing")
        with pytest.raises(Unavailable):
            create(setup, key="second_request_000000")
        executor.step()
        assert setup.controller.get(setup.actor, job.job_id).status == "failed"
        assert (directory / "keep.txt").read_text() == "existing"
    finally:
        executor.close()


def test_queue_capacity_and_real_queue_metric(setup):
    settings = setup.settings.model_copy(update={"max_queued": 1})
    setup.controller = Controller(settings)
    setup.app = Application(setup.controller)
    executor = Executor(settings)
    try:
        create(setup)
        with pytest.raises(Unavailable, match="capacity"):
            create(setup, key="second_queue_request_0000")
        metrics = api(setup, "GET", "/v1/metrics")[1]
        assert (
            'personal_assistant_queue_jobs{process="material_planning",worker_pool="default"} 1'
            in metrics
        )
    finally:
        executor.close()


def test_logs_bounded_filtered_and_no_raw_input_echo(setup):
    job = create(setup, start=False)
    logs = setup.controller.store.logs(job.job_id, limit=1)
    assert len(logs["events"]) == 1
    assert setup.controller.store.logs(job.job_id, query="NO-MATCH")["events"] == []
    assert len(json.dumps(logs).encode()) < 16000
    for key in ("token", "password", "Authorization"):
        status, value = api(
            setup,
            "POST",
            "/v1/previews",
            dict(process_id="material_planning", parameters={key: "DO-NOT-ECHO"}),
        )
        assert status == 422 and "DO-NOT-ECHO" not in json.dumps(value)
    assert api(setup, "GET", "/v1/jobs/" + job.job_id + "/logs?limit=100000")[0] == 422


def test_private_paths_symlinks_and_schema_version(setup):
    link = setup.tmp / "linked"
    link.symlink_to(setup.settings.root, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink"):
        Store(link)
    with pytest.raises(ValueError):
        safe_path(setup.settings.root, "../outside")
    with setup.controller.store.connection() as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(ValueError, match="version"):
        Store(setup.settings.root)


def test_catalog_hash_symlink_and_foreign_scope_fail_closed(setup):
    entry = setup.settings.catalog["demo_snapshots"]
    source = entry.root / "cs50_python/week0.html"
    original = source.read_bytes()
    source.unlink()
    target = setup.tmp / "unapproved.html"
    target.write_bytes(original)
    source.symlink_to(target)
    with pytest.raises(ValueError, match="Symlink"):
        request_data(setup)
    assert setup.controller.history(setup.settings.identities[-1]) == []
    with pytest.raises(ValidationError):
        type(entry).model_validate(
            {**entry.model_dump(), "files": {"../outside": "0" * 64}}
        )


def test_log_cursor_paginates_under_search_and_limits(setup):
    job = create(setup, start=False)
    with setup.controller.store.connection(write=True) as db:
        for _ in range(220):
            setup.controller.store.put_db(db, job, "Synthetic bounded event")
    page = setup.controller.store.logs(job.job_id, limit=200)
    assert len(page["events"]) <= 200 and page["truncated"]
    assert len(encode(page)) <= 16000
    rest = setup.controller.store.logs(
        job.job_id, cursor=page["next_cursor"], limit=200
    )
    assert rest["events"] and rest["events"][0]["sequence"] > page["next_cursor"]
    filtered = setup.controller.store.logs(job.job_id, query="unmatched")
    assert filtered["truncated"] and filtered["next_cursor"] > 0


def test_course_scope_applies_to_logs_artifacts_and_metrics(setup):
    from src.job_control.store import now

    job = create(setup, start=False)
    setup.controller.store.transition(
        job.job_id, "queued", "queued", "Synthetic queued state"
    )
    setup.controller.store.transition(
        job.job_id,
        "running",
        "offline_adapter",
        "Synthetic running observation",
        started_at=now(),
    )
    foreign = {"Authorization": "Bearer synthetic_foreign_token_00000000000000000"}
    for suffix in ("", "/logs", "/artifacts"):
        assert (
            api(setup, "GET", "/v1/jobs/" + job.job_id + suffix, headers=foreign)[0]
            == 403
        )
    local_metrics = api(setup, "GET", "/v1/metrics")[1]
    foreign_metrics = api(setup, "GET", "/v1/metrics", headers=foreign)[1]
    series = 'personal_assistant_jobs_running{process="material_planning",worker_pool="default"}'
    assert series + " 1" in local_metrics and series + " 0" in foreign_metrics


def test_concurrent_store_initialization(tmp_path):
    root = tmp_path / "concurrent-private"
    with ThreadPoolExecutor(max_workers=4) as pool:
        stores = list(pool.map(lambda _: Store(root), range(4)))
    assert all(s.all() == () for s in stores)


def test_foreign_database_is_not_changed_or_adopted(tmp_path):
    root = tmp_path / "foreign-private"
    root.mkdir(mode=0o700)
    path = root / "jobs.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE unrelated(value TEXT)")
        db.execute("INSERT INTO unrelated VALUES('synthetic keep')")
    original = path.read_bytes()
    with pytest.raises(ValueError, match="Foreign"):
        Store(root)
    assert path.read_bytes() == original
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "delete"


def test_transport_contract_snapshot():
    from src.job_control import models

    snapshot = json.loads(
        (
            Path(__file__).resolve().parents[1] / "docs/job_control/contract.v1.json"
        ).read_text()
    )
    assert snapshot["registry"] == registry_document()
    for name, schema in snapshot["models"].items():
        assert schema == getattr(models, name).model_json_schema()


def test_unknown_request_version_is_rejected(setup):
    status, _ = api(
        setup,
        "POST",
        "/v1/previews",
        dict(schema_version=2, process_id="material_planning", parameters={}),
    )
    assert status == 422
    with pytest.raises(ValidationError):
        from src.job_control.models import StartRequest

        StartRequest.model_validate({**request_data(setup), "schema_version": 2})


@pytest.mark.parametrize("confirmed", [False, 1, "true", None])
def test_confirmation_is_strict_boolean(setup, confirmed):
    body = request_data(setup)
    with pytest.raises(ValidationError):
        setup.controller.create(
            setup.actor, {**body, "confirmed": confirmed}, "strict_confirmation_00"
        )


class MemorySocket:
    def __init__(self, request):
        self.input = io.BytesIO(request)
        self.output = bytearray()

    def settimeout(self, value):
        pass

    def makefile(self, mode, *args):
        return self.input

    def sendall(self, value):
        self.output.extend(value)


def test_actual_http_handler_without_socket_or_server(setup):
    request = MemorySocket(
        (
            "GET /v1/processes HTTP/1.0\r\nAuthorization: Bearer "
            + DEMO_TOKEN
            + "\r\n\r\n"
        ).encode()
    )
    handler_for(setup.app)(request, ("127.0.0.1", 1), SimpleNamespace())
    assert b"200 OK" in request.output and b"material_planning" in request.output
    request = MemorySocket(
        b"POST /v1/jobs HTTP/1.0\r\nContent-Length: 1\r\nContent-Length: 2\r\n\r\n{}"
    )
    handler_for(setup.app)(request, ("127.0.0.1", 1), SimpleNamespace())
    assert b"400 Bad Request" in request.output
