"""Real C23 gates and C16 workers; no real source bundles or external services."""

import json
import socket

import pytest

from src.job_control.executor import Executor
from tests.content_import_support import (
    IMPORT,
    KEY,
    api,
    create,
    finish,
    preview,
    setup,
)
from tests.content_store_support import OTHER, OWNER, VIEWER


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*a, **kw):
        raise AssertionError("Network forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.mark.parametrize("kind", ["code", "html", "pdf", "srt"])
def test_real_gates_worker_and_original_byte_roundtrip(tmp_path, kind):
    env = setup(tmp_path, kind)
    assert (
        api(env, "GET", IMPORT + "inputs")["items"][0]["input_ref"]
        == "synthetic-import"
    )
    assert not api(env, "GET", "/v1/content/sources")["items"]
    p = preview(env)
    assert p["plan"]["can_import"] and p["plan"]["existing_parsed_version_id"] is None
    assert str(tmp_path) not in json.dumps(p)
    executor = Executor(env.settings)
    try:
        job = create(env, p=p)
        done = finish(env, executor, job, timeout=25)
        assert done.status == "completed", done
        assert done.artifact_refs[0].kind == "content_import"
        assert api(env, "GET", IMPORT + "result?job_id=" + job["job_id"])["created"]
        assert create(env, p=p)["job_id"] == job["job_id"]
        assert len(api(env, "GET", "/v1/content/sources")["items"]) == 1
        current = preview(env, "synthetic_import_request_0002")
        assert (
            current["plan"]["existing_parsed_version_id"]
            == p["plan"]["parsed_version_id"]
        )
        assert current["plan"]["source_version_id"] == p["plan"]["source_version_id"]
        retry = create(env, "synthetic_import_request_0002", p=current)
        assert finish(env, executor, retry, timeout=25).status == "completed"
        receipt = json.loads(
            (
                env.controller.store.directory(retry["job_id"])
                / "results/content-import.json"
            ).read_bytes()
        )
        assert not receipt["created"]
        parsed = api(env, "GET", receipt["parsed_route"])
        assert parsed["parsed_version_id"] == p["plan"]["parsed_version_id"]
        assert (
            env.content.read_raw_artifact(
                receipt["source_id"], receipt["raw_sha256"], actor=OWNER
            )
            == env.bundle.raw_path.read_bytes()
        )
        payload = (
            getattr(env.bundle, "normalized_path", None) or env.bundle.transcript_path
        )
        assert (
            env.content.read_parsed_payload(receipt["parsed_version_id"], actor=OWNER)
            == payload.read_bytes()
        )
    finally:
        executor.close()


def test_permissions_and_tampered_confirmation(tmp_path):
    env = setup(tmp_path)
    for actor in (VIEWER, OTHER):
        assert not api(env, "GET", IMPORT + "inputs", actor=actor)["items"]
        preview(env, actor=actor, expected=404)
    p = preview(env)
    p["preview"]["parameters"]["state_sha256"] = "0" * 64
    create(env, p=p, expected=409)
    p = preview(env)
    create(env, key="synthetic_import_other_key", p=p, expected=422)


def test_changed_pinned_input_is_rejected_before_dispatch(tmp_path):
    env = setup(tmp_path)
    executor = Executor(env.settings)
    try:
        job = create(env)
        env.bundle.raw_path.write_bytes(b"changed")
        done = finish(env, executor, job, timeout=20)
        assert done.status == "failed"
        assert not api(env, "GET", "/v1/content/sources")["items"]
    finally:
        executor.close()


@pytest.mark.parametrize("phase", ["before_publication", "after_publication"])
def test_actual_sigkill_and_explicit_recovery_boundary(tmp_path, phase):
    import subprocess
    import sys
    import time

    env = setup(tmp_path)
    env.controller.store.heartbeat()
    p = preview(env)
    job = create(env, p=p)
    child = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "tests.content_import_probe",
            "--root",
            str(env.settings.root),
            "--job",
            job["job_id"],
            "--phase",
            phase,
        ]
    )
    try:
        until = time.monotonic() + 35
        while not (env.settings.root / "probe-ready").exists():
            assert child.poll() is None
            assert time.monotonic() < until
            time.sleep(0.05)
        child.kill()
        child.wait(timeout=5)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
    executor = Executor(env.settings)
    try:
        assert env.controller.store.get(job["job_id"]).status == "interrupted"
        assert create(env, p=p)["job_id"] == job["job_id"]
        api(env, "GET", IMPORT + "result?job_id=" + job["job_id"], expected=409)
        next_plan = preview(env, "synthetic_import_after_crash")
        if phase == "before_publication":
            assert not next_plan["plan"]["can_import"]
            assert next_plan["preview"] is None
            assert next_plan["plan"]["operator_decision"] == "content_recovery_required"
            assert next_plan["plan"]["existing_parsed_version_id"] is None
        else:
            assert (
                next_plan["plan"]["existing_parsed_version_id"]
                == p["plan"]["parsed_version_id"]
            )
            retry = create(env, "synthetic_import_after_crash", p=next_plan)
            assert finish(env, executor, retry, timeout=25).status == "completed"
            assert not api(env, "GET", IMPORT + "result?job_id=" + retry["job_id"])[
                "created"
            ]
    finally:
        executor.close()


def test_timeout_same_key_never_reexecutes_and_explicit_new_plan(tmp_path):
    import subprocess
    import sys

    env = setup(tmp_path)
    env.controller.store.heartbeat()
    p = preview(env)
    job = create(env, p=p)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "tests.content_import_probe",
            "--root",
            str(env.settings.root),
            "--job",
            job["job_id"],
            "--phase",
            "timeout",
        ],
        check=True,
        timeout=15,
    )
    executor = Executor(env.settings)
    try:
        done = env.controller.store.get(job["job_id"])
        assert done.status == "failed" and done.error_class == "timeout"
        assert create(env, p=p)["job_id"] == done.job_id
        retry = create(env, "synthetic_import_timeout_retry")
        assert finish(env, executor, retry, timeout=25).status == "completed"
    finally:
        executor.close()


def test_import_explicit_index_search_restart_and_acl(tmp_path):
    from src.content_store.models import SourceGrant
    from src.job_control.controller import Controller
    from src.job_control.http import Application
    from tests.content_import_support import add_index
    from tests.index_job_support import create as create_index

    env = add_index(setup(tmp_path))
    assert not api(env, "GET", "/v1/content/index/inputs")["items"]
    p = preview(env)
    executor = Executor(env.settings)
    try:
        done = finish(env, executor, create(env, p=p), timeout=25)
        assert done.status == "completed"
        receipt = api(env, "GET", IMPORT + "result?job_id=" + done.job_id)
        assert receipt["parsed_version_id"] == p["plan"]["parsed_version_id"]
        assert env.index._active()[1] is None
        assert not api(
            env, "POST", "/v1/content/search", dict(schema_version=1, query="hello")
        )["items"]
        indexed = finish(env, executor, create_index(env), timeout=25)
        assert indexed.status == "completed"
        hits = api(
            env, "POST", "/v1/content/search", dict(schema_version=1, query="hello")
        )["items"]
        assert hits and hits[0]["source_id"] == receipt["source_id"]
    finally:
        executor.close()
    env.controller = Controller(env.settings)
    env.app = Application(
        env.controller, content_settings=env.read, search_settings=env.search
    )
    assert api(env, "GET", IMPORT + "result?job_id=" + done.job_id) == receipt
    assert (
        api(env, "POST", "/v1/content/search", dict(schema_version=1, query="hello"))[
            "items"
        ]
        == hits
    )
    source = env.content.get_source(receipt["source_id"], actor=OWNER)
    env.content.set_source_grants(
        source.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=source.acl_revision,
        actor=OWNER,
    )
    assert api(env, "GET", "/v1/content/sources", actor=VIEWER)["items"]
    assert not api(env, "GET", IMPORT + "inputs", actor=VIEWER)["items"]
    api(env, "GET", "/v1/jobs/" + done.job_id, actor=VIEWER, expected=404)
    source = env.content.get_source(source.source_id, actor=OWNER)
    env.content.set_source_grants(
        source.source_id, (), expected_acl_revision=source.acl_revision, actor=OWNER
    )
    assert not api(env, "GET", "/v1/content/sources", actor=VIEWER)["items"]
    assert not api(
        env,
        "POST",
        "/v1/content/search",
        dict(schema_version=1, query="hello"),
        actor=VIEWER,
    )["items"]


@pytest.mark.parametrize(
    "fault", ["revision", "payload_type", "missing_receipt", "oversize", "wrong_origin"]
)
def test_approved_bytes_still_must_pass_real_gates(tmp_path, fault):
    from src.content_store.models import canonical, sha256
    from src.job_control.controller import Controller
    from src.job_control.http import Application

    env = setup(tmp_path)
    if fault == "missing_receipt":
        env.bundle.receipt_path.unlink()
        preview(env, expected=422)
        return
    if fault == "oversize":
        env.bundle.raw_path.write_bytes(b"x" * (8 * 1024 * 1024 + 1))
        preview(env, expected=422)
        return
    path = (
        env.bundle.implementation_path
        if fault == "revision"
        else env.bundle.normalized_path
    )
    value = json.loads(path.read_bytes())
    if fault == "revision":
        value["implementation_revision"] = "b" * 40
    elif fault == "payload_type":
        value["schema_version"] = 999
    else:
        value["binding"]["source_origin"] = "official"
    path.write_bytes(canonical(value))
    files = {
        **env.entry.files,
        path.relative_to(env.entry.root).as_posix(): sha256(path.read_bytes()),
    }
    entry = env.entry.model_copy(update={"files": files})
    settings = env.settings.model_copy(update={"catalog": {"synthetic-import": entry}})
    env.app = Application(Controller(settings), content_settings=env.read)
    preview(env, expected=409)
    assert not api(env, "GET", "/v1/content/sources")["items"]


def test_cancel_and_corrupt_receipt(tmp_path):
    from src.job_control.controller import Controller
    from src.job_control.http import Application

    env = setup(tmp_path)
    env.controller.store.heartbeat()
    p = preview(env)
    job = create(env, p=p)
    env.controller.cancel(OWNER, job["job_id"])
    executor = Executor(env.settings)
    try:
        assert env.controller.store.get(job["job_id"]).status == "cancelled"
        next_job = create(env, "synthetic_import_after_cancel")
        done = finish(env, executor, next_job, timeout=25)
        assert done.status == "completed"
    finally:
        executor.close()
    receipt = (
        env.controller.store.directory(done.job_id) / "results/content-import.json"
    )
    receipt.write_bytes(b"corrupt")
    api(env, "GET", IMPORT + "result?job_id=" + done.job_id, expected=409)
    with env.content._connection(write=True) as db:
        db.execute("UPDATE parsed_versions SET state='quarantined'")
    preview(env, expected=404)
    assert api(env, "GET", "/v1/content/sources")["items"]
    with env.content._connection(write=True) as db:
        db.execute("UPDATE sources SET state='tombstoned'")
    assert not api(env, "GET", IMPORT + "inputs")["items"]
    api(env, "GET", "/v1/jobs/" + done.job_id, expected=404)
    env.controller = Controller(env.settings)
    env.app = Application(env.controller, content_settings=env.read)


def test_delivery_guard_and_unknown_schema(tmp_path):
    from src.content_store.errors import Busy
    from tests.index_job_support import token

    env = setup(tmp_path)
    response = env.app.request(
        "GET", IMPORT + "inputs", {"Authorization": "Bearer " + token(OWNER)}
    )
    try:
        with pytest.raises(Busy):
            with env.content._artifacts.lock(
                ".content-maintenance.lock", exclusive=True
            ):
                pass
    finally:
        response.close()
    api(
        env,
        "POST",
        IMPORT + "preview",
        dict(schema_version=2, input_ref="synthetic-import", request_key=KEY),
        expected=422,
    )
    api(
        env,
        "POST",
        IMPORT + "preview",
        dict(schema_version=1, input_ref="/tmp/arbitrary", request_key=KEY),
        expected=404,
    )
    api(env, "GET", IMPORT + "inputs?offset=1001", expected=422)
    api(env, "GET", IMPORT + "inputs?offset=0&offset=1", expected=422)


def test_dispatch_rechecks_current_identity_role(tmp_path):
    env = setup(tmp_path)
    env.controller.store.heartbeat()
    job = create(env)
    settings = env.settings.model_copy(
        update={
            "identities": tuple(
                i.model_copy(update={"role": "viewer"})
                if i.subject == OWNER.subject
                else i
                for i in env.settings.identities
            )
        }
    )
    executor = Executor(settings)
    try:
        done = finish(env, executor, job)
        assert done.status == "failed" and done.error_class == "input"
        assert not api(env, "GET", "/v1/content/sources")["items"]
    finally:
        executor.close()
