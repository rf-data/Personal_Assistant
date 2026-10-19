"""Actual C16 job -> FTS5 -> scoped status/search; synthetic private roots only."""

import socket
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

from src.content_store.errors import Busy, Forbidden, InvalidInput
from src.content_store.models import SourceGrant
from src.job_control.executor import Executor
from src.job_control.index_models import IndexJobPlan, IndexStatus
from src.tools_rag.content_index_models import SearchResultPage
from tests.content_store_support import OTHER, OWNER, VIEWER
from tests.index_job_support import INDEX, api, create, finish, preview, setup, status


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*a, **kw):
        raise AssertionError("Network forbidden in index job tests")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.fixture
def env(tmp_path):
    return setup(tmp_path)


def test_actual_job_activation_receipt_http_search_and_restart(env):
    assert status(env)["state"] == "not_indexed"
    assert api(env, "GET", INDEX + "inputs")["items"][0]["can_build"]
    executor = Executor(env.settings)
    try:
        job = create(env)
        assert job["status"] == "queued"
        done = finish(env, executor, job)
        assert done.status == "completed", done
        assert done.artifact_refs[0].kind == "index_build"
        state = IndexStatus.model_validate(status(env))
        assert state.state == "active" and state.latest_activation == "committed"
        assert (
            state.receipt.outcome == "activated" and state.receipt.job_id == done.job_id
        )
        assert state.receipt.build_id == done.job_id[4:]
        page = SearchResultPage.model_validate(
            api(
                env, "POST", "/v1/content/search", dict(schema_version=1, query="hello")
            )
        )
        assert len(page.items) == 3 and page.index_generation == state.index_generation
        assert str(env.tmp) not in state.model_dump_json()
        assert (
            "cursor_key" not in state.model_dump_json()
            and "snapshot" not in state.receipt.model_dump_json()
        )
    finally:
        executor.close()
    from src.job_control.controller import Controller
    from src.job_control.http import Application

    env.controller = Controller(env.settings)
    env.app = Application(
        env.controller,
        content_settings=env.spec.content,
        search_settings=env.spec.search,
    )
    assert status(env)["state"] == "active"
    assert api(env, "GET", "/v1/jobs/" + done.job_id)["status"] == "completed"


def test_duplicate_requests_share_one_job_and_changed_intent_conflicts(env):
    env.controller.store.heartbeat()
    p = preview(env)
    request = dict(schema_version=1, preview=p, confirmed=True, start=False)
    key = "synthetic_concurrent_index_key"

    def call(_):
        return env.controller.create(OWNER, request, key)

    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = list(pool.map(call, range(3)))
    assert len({j.job_id for j in jobs}) == 1 and len(env.controller.store.all()) == 1
    api(env, "POST", "/v1/jobs", request | {"start": True}, key=key, expected=409)
    assert status(env)["state"] == "not_indexed"


def test_source_and_course_scope_hide_inputs_jobs_and_status_after_revocation(env):
    assert not api(env, "GET", INDEX + "inputs", actor=OTHER)["items"]
    status(env, actor=OTHER, expected=404)
    preview(env, actor=OTHER, expected=403)
    preview(env, actor=VIEWER, expected=403)
    executor = Executor(env.settings)
    try:
        job = create(env)
        done = finish(env, executor, job)
        assert done.status == "completed"
    finally:
        executor.close()
    api(env, "GET", "/v1/jobs/" + job["job_id"], actor=OTHER, expected=404)
    assert not api(env, "GET", "/v1/jobs", actor=OTHER)
    env.content.set_source_grants(
        env.pv.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert status(env, actor=VIEWER)["state"] == "active"
    assert not api(env, "GET", INDEX + "inputs", actor=VIEWER)["items"][0]["can_build"]
    assert (
        api(env, "GET", "/v1/jobs/" + job["job_id"], actor=VIEWER)["status"]
        == "completed"
    )
    env.content.set_source_grants(
        env.pv.source_id, (), expected_acl_revision=1, actor=OWNER
    )
    status(env, actor=VIEWER, expected=404)
    assert not api(env, "GET", INDEX + "inputs", actor=VIEWER)["items"]
    api(env, "GET", "/v1/jobs/" + job["job_id"], actor=VIEWER, expected=404)
    assert not api(env, "GET", "/v1/jobs", actor=VIEWER)
    assert not api(
        env,
        "POST",
        "/v1/content/search",
        dict(schema_version=1, query="hello"),
        actor=VIEWER,
    )["items"]


@pytest.mark.parametrize("state", ["quarantined", "tombstoned"])
def test_version_status_blocks_preview_and_status(env, state):
    env.index.build(env.spec.selection, actor=OWNER)
    with env.content._maintenance(), env.content._connection(write=True) as db:
        db.execute(
            "UPDATE parsed_versions SET state=? WHERE id=?",
            (state, env.pv.parsed_version_id),
        )
    assert status(env)["state"] == "blocked"
    preview(env, expected=403)
    api(
        env,
        "POST",
        "/v1/content/search",
        dict(schema_version=1, query="hello"),
        expected=409,
    )


def test_worker_rechecks_tombstone_after_queue_admission(env):
    env.controller.store.heartbeat()
    job = create(env)
    with env.content._maintenance(), env.content._connection(write=True) as db:
        db.execute(
            "UPDATE parsed_versions SET state='quarantined' WHERE id=?",
            (env.pv.parsed_version_id,),
        )
    executor = Executor(env.settings)
    try:
        assert finish(env, executor, job).status == "failed"
    finally:
        executor.close()
    assert env.index._active()[1] is None
    assert status(env)["state"] == "blocked"


def test_disabled_configuration_and_request_limits(env):
    from src.job_control.controller import Controller
    from src.job_control.http import Application

    disabled = env.settings.model_copy(update={"index_jobs_enabled": False})
    env.app = Application(
        Controller(disabled),
        content_settings=env.spec.content,
        search_settings=env.spec.search,
    )
    assert not api(env, "GET", INDEX + "capabilities")["enabled"]
    api(env, "GET", INDEX + "inputs", expected=503)
    preview(env, expected=403)
    with pytest.raises(ValueError):
        Application(Controller(env.settings))


def test_plan_schema_and_pinned_identity(env):
    spec = env.spec.model_dump(mode="json")
    for change in [
        dict(schema_version=2),
        dict(schema_version=True),
        dict(versions=[]),
        dict(versions=spec["versions"] * 33),
        dict(extra="private"),
    ]:
        with pytest.raises(ValidationError):
            IndexJobPlan.model_validate(spec | change)
    changed = env.spec.model_copy(
        update={
            "versions": (
                env.spec.versions[0].model_copy(update={"payload_sha256": "f" * 64}),
            )
        }
    )
    from src.content_store.errors import IntegrityError
    from src.job_control.index_jobs import verify

    with pytest.raises(IntegrityError):
        verify(changed, OWNER)


def test_distinct_jobs_same_version_are_serialized_by_existing_queue(env):
    executor = Executor(env.settings)
    try:
        first = create(env, key="synthetic_first_index_key")
        second = create(env, key="synthetic_second_index_key")
        assert first["job_id"] != second["job_id"]
        assert finish(env, executor, first).status == "completed"
        assert finish(env, executor, second).status == "completed"
    finally:
        executor.close()
    receipts = env.index.inspect_builds(actor=OWNER)
    assert {r.state for r in receipts} == {"active", "retired"}
    assert len({r.generation_id for r in receipts}) == 1
    assert status(env)["state"] == "active"


def test_status_and_generic_job_metadata_hold_live_authorization_guard(env):
    env.controller.store.heartbeat()
    job = create(env, start=False)
    for path in [
        INDEX + "inputs",
        INDEX + "status?input_ref=synthetic-index",
        "/v1/jobs/" + job["job_id"],
        "/v1/jobs",
    ]:
        from tests.index_job_support import token

        reply = env.app.request(
            "GET", path, {"Authorization": "Bearer " + token(OWNER)}
        )
        assert reply.status == 200
        try:
            with pytest.raises(Busy):
                env.content.set_source_grants(
                    env.pv.source_id, (), expected_acl_revision=0, actor=OWNER
                )
        finally:
            reply.close()
    env.content.set_source_grants(
        env.pv.source_id, (), expected_acl_revision=0, actor=OWNER
    )


@pytest.mark.parametrize("phase", ["before_activation", "after_activation"])
def test_sigkill_retry_and_response_loss_are_fail_closed(env, phase):
    import subprocess
    import sys

    env.controller.store.heartbeat()
    job = create(env)
    child = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "tests.index_job_probe",
            "--root",
            str(env.settings.root),
            "--job",
            job["job_id"],
            "--phase",
            phase,
        ]
    )
    try:
        until = time.monotonic() + 12
        marker = env.settings.root / "probe-ready"
        while not marker.exists():
            assert child.poll() is None
            assert time.monotonic() < until
            time.sleep(0.03)
        child.kill()
        child.wait(timeout=5)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
    executor = Executor(env.settings)
    try:
        prior = env.controller.store.get(job["job_id"])
        assert prior.status == "interrupted"
        assert create(env)["job_id"] == prior.job_id  # Same key never reruns.
        old_active = env.index.files.read("active.json", missing=True)
        current = status(env)
        if phase == "before_activation":
            assert (
                current["state"] == "failed"
                and current["latest_activation"] == "not_committed"
            )
            assert old_active is None
        else:
            assert (
                current["state"] == "active"
                and current["latest_activation"] == "committed"
            )
            assert old_active
        retry = create(env, key="synthetic_explicit_retry_key", resume_of=prior.job_id)
        completed = finish(env, executor, retry)
        assert completed.status == "completed", completed
        current = status(env)
        assert (
            current["state"] == "active" and current["latest_activation"] == "committed"
        )
        assert current["receipt"]["outcome"] == (
            "already_active" if phase == "after_activation" else "activated"
        )
        if phase == "after_activation":
            assert env.index.files.read("active.json") == old_active
        else:
            assert env.index.files.read("active.json") != old_active
            assert (
                env.index.root / "staging" / prior.job_id[4:] / "manifest.json"
            ).exists()
    finally:
        executor.close()


@pytest.mark.parametrize("phase", ["staging_error", "timeout"])
def test_staging_failure_and_actual_guardian_timeout(env, phase):
    import subprocess
    import sys

    env.controller.store.heartbeat()
    job = create(env)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tests.index_job_probe",
            "--root",
            str(env.settings.root),
            "--job",
            job["job_id"],
            "--phase",
            phase,
        ],
        timeout=12,
    )
    assert result.returncode == (3 if phase == "staging_error" else 0)
    executor = Executor(env.settings)
    try:
        current = env.controller.store.get(job["job_id"])
        if phase == "timeout":
            assert current.status == "failed" and current.error_class == "timeout"
        else:
            assert current.status == "interrupted"
        assert env.index._active()[1] is None
        assert status(env)["state"] == "failed"
    finally:
        executor.close()


def test_no_operator_may_replace_foreign_active_generation(env):
    from src.content_store.adapters import import_verified_bundle, verify_srt_bundle
    from src.tools_rag.content_index_models import IndexSelection
    from tests.content_adapter_support import srt

    root = env.tmp / "other"
    root.mkdir()
    bundle, _ = srt(root)
    foreign = import_verified_bundle(
        env.content, verify_srt_bundle(bundle), actor=OTHER, request_key="other"
    ).version
    env.index.build(
        IndexSelection(parsed_version_ids=(foreign.parsed_version_id,)), actor=OTHER
    )
    before = env.index.files.read("active.json")
    with pytest.raises(Forbidden):
        env.index.build(env.spec.selection, actor=OWNER)
    assert env.index.files.read("active.json") == before
    preview(env, expected=403)
    inputs = api(env, "GET", INDEX + "inputs")["items"]
    assert inputs and not inputs[0]["can_build"]
    assert foreign.source_id not in str(inputs)


def test_dispatch_rejects_current_role_revocation(env):
    env.controller.store.heartbeat()
    job = create(env)
    identities = tuple(
        a.model_copy(update={"role": "viewer"}) if a.subject == OWNER.subject else a
        for a in env.settings.identities
    )
    settings = env.settings.model_copy(update={"identities": identities})
    executor = Executor(settings)
    try:
        current = finish(env, executor, job)
        assert current.status == "failed" and current.error_class == "input"
        assert env.index._active()[1] is None
    finally:
        executor.close()


def test_corrupt_partition_is_blocked_and_receipt_hashes_checked(env):
    executor = Executor(env.settings)
    try:
        job = create(env)
        done = finish(env, executor, job)
        assert done.status == "completed"
    finally:
        executor.close()
    _, active, manifest = env.index._active()
    file = (
        env.index.root
        / "generations"
        / active.generation_id.split(":")[1]
        / active.build_id
        / manifest.files[0].name
    )
    file.write_bytes(b"corrupt private synthetic index")
    assert status(env)["state"] == "blocked"
    receipt = env.controller.store.directory(job["job_id"]) / "results/index-build.json"
    receipt.write_bytes(b"corrupt receipt")
    status(env, expected=503)


def test_build_identity_no_overwrite_and_request_bounds(env):
    receipt = env.index.build(env.spec.selection, actor=OWNER, build_id="a" * 32)
    assert receipt.build_id == "a" * 32
    with pytest.raises(InvalidInput):
        env.index.build(env.spec.selection, actor=OWNER, build_id="a" * 32)
    for bid in ["../escape", "x" * 32, "a" * 31]:
        with pytest.raises(InvalidInput):
            env.index.build(env.spec.selection, actor=OWNER, build_id=bid)
    for suffix in [
        "inputs?limit=11",
        "inputs?offset=-1",
        "status?input_ref=synthetic-index&limit=21",
        "inputs?sql=SELECT",
        "inputs?offset=0&offset=1",
    ]:
        api(env, "GET", INDEX + suffix, expected=422)
    api(env, "POST", INDEX + "status", {}, expected=405)


def test_rejected_live_generation_never_reports_verified_generation(env, monkeypatch):
    from src.tools_rag.content_index import ContentIndex

    executor = Executor(env.settings)
    try:
        done = finish(env, executor, create(env))
        assert done.status == "completed"
    finally:
        executor.close()
    original = ContentIndex._search

    def mismatched_generation(self, *args, **kwargs):
        page = original(self, *args, **kwargs)
        return page.model_copy(update={"index_generation": None})

    monkeypatch.setattr(ContentIndex, "_search", mismatched_generation)
    report = status(env)
    assert report["state"] == "blocked"
    assert report["index_generation"] is None
