"""Separate actual loopback HTTP evidence from in-process handler evidence."""

import io
import json
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from email.message import Message
from http.server import HTTPServer
from pathlib import Path
from threading import Event, Thread
from types import SimpleNamespace

import httpx
import pytest

from src.content_store.errors import Busy
from src.content_store.models import SourceGrant, canonical
from src.content_store.search_http import SearchReply
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.http import Application, handler_for
from tests.content_store_support import OWNER, VIEWER
from tests.index_job_support import INDEX, api, create, finish, setup, token
from tests.test_content_fts import inventory


@pytest.fixture(autouse=True)
def local_only(monkeypatch):
    connect = socket.socket.connect
    resolve = socket.getaddrinfo

    def local(sock, address):
        assert address[0] == "127.0.0.1"
        return connect(sock, address)

    monkeypatch.setattr(socket.socket, "connect", local)

    def local_resolve(host, *args, **kwargs):
        assert host == "127.0.0.1"
        return resolve(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", local_resolve)


def handler_exchange(
    app, method, path, value=None, *, actor=OWNER, key=None, output=None
):
    """Execute the real HTTP handler over byte streams, without claiming a socket."""
    handler = object.__new__(handler_for(app))
    handler.command, handler.path = method, path
    body = canonical(value) if value is not None else b""
    handler.headers = Message()
    for name, value in {
        "Authorization": "Bearer " + token(actor),
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
        **({"Idempotency-Key": key} if key else {}),
    }.items():
        handler.headers[name] = value
    handler.rfile = io.BytesIO(body)
    handler.wfile = io.BytesIO() if output is None else output
    handler.connection = SimpleNamespace(settimeout=lambda seconds: None)
    handler.request_version = "HTTP/1.1"
    handler.requestline = method + " " + path + " HTTP/1.1"
    handler.handle_request()
    headers, raw = handler.wfile.getvalue().split(b"\r\n\r\n", 1)
    assert b"Cache-Control: no-store" in headers
    return int(headers.split()[1]), json.loads(raw)


def exercise(env, exchange):
    before = inventory(env.bundle.workspace)
    with _executor(env.settings) as worker:
        code, preview = exchange(
            "POST",
            "/v1/previews",
            dict(
                schema_version=1,
                process_id="content_index_build",
                parameters=dict(
                    schema_version=1,
                    source_ref="synthetic-index",
                    course_id="cs50_python",
                ),
            ),
        )
        assert code == 200
        request = dict(schema_version=1, preview=preview, confirmed=True, start=True)
        code, job = exchange("POST", "/v1/jobs", request, key="c24r_http_e2e_0001")
        assert code == 202
        assert finish(env, worker, job).status == "completed"
        code, state = exchange("GET", INDEX + "status?input_ref=synthetic-index")
        assert code == 200 and state["latest_activation"] == "committed"
        env.content.set_source_grants(
            env.pv.source_id,
            (SourceGrant(subject=VIEWER.subject),),
            expected_acl_revision=0,
            actor=OWNER,
        )
        code, page = exchange(
            "POST",
            "/v1/content/search",
            dict(schema_version=1, query="hello", limit=1),
            actor=VIEWER,
        )
        assert code == 200 and len(page["items"]) == 1 and page["next_cursor"]
        hit = page["items"][0]
        assert hit["source_id"] == env.pv.source_id
        assert hit["parsed_version_id"] == env.pv.parsed_version_id
        assert page["index_generation"] == state["index_generation"]
        env.content.set_source_grants(
            env.pv.source_id, (), expected_acl_revision=1, actor=OWNER
        )
        code, revoked = exchange(
            "POST",
            "/v1/content/search",
            dict(schema_version=1, query="hello"),
            actor=VIEWER,
        )
        assert code == 200 and revoked["items"] == []
        # Same accepted intent never dispatches a second build.
        code, replay = exchange("POST", "/v1/jobs", request, key="c24r_http_e2e_0001")
        assert code == 202 and replay["job_id"] == job["job_id"]
    assert inventory(env.bundle.workspace) == before
    return state["index_generation"]


@contextmanager
def _executor(settings):
    worker = Executor(settings)
    try:
        yield worker
    finally:
        worker.close()


def test_handler_job_to_search_revocation_and_reopen(tmp_path):
    env = setup(tmp_path)
    generation = exercise(env, lambda *a, **kw: handler_exchange(env.app, *a, **kw))
    env.controller = Controller(env.settings)
    env.app = Application(
        env.controller,
        content_settings=env.spec.content,
        search_settings=env.spec.search,
    )
    code, page = handler_exchange(
        env.app, "POST", "/v1/content/search", dict(schema_version=1, query="hello")
    )
    assert code == 200 and page["index_generation"] == generation and page["items"]


def test_status_body_can_arrive_before_handler_releases_lock(tmp_path, monkeypatch):
    """Threaded handler evidence only: complete bytes do not imply guard cleanup."""
    env = setup(tmp_path)
    output = io.BytesIO()
    closing, release = Event(), Event()
    close = SearchReply.close

    def paused_close(reply):
        closing.set()
        try:
            assert release.wait(timeout=3), "test did not release response cleanup"
        finally:
            close(reply)

    monkeypatch.setattr(SearchReply, "close", paused_close)
    # No job or worker is needed to reproduce the cross-thread lock conflict.
    assert env.controller.store.all() == ()
    with ThreadPoolExecutor(max_workers=1) as pool:
        response = pool.submit(
            handler_exchange,
            env.app,
            "GET",
            INDEX + "status?input_ref=synthetic-index",
            output=output,
        )
        try:
            assert closing.wait(timeout=3), "handler did not reach response cleanup"
            headers, raw = output.getvalue().split(b"\r\n\r\n", 1)
            assert b"Content-Length: " + str(len(raw)).encode() + b"\r\n" in headers
            assert json.loads(raw)["state"] == "not_indexed"
            with pytest.raises(Busy, match="content lock held"):
                with env.content._artifacts.lock(".content-db.lock", exclusive=True):
                    pytest.fail("status response guard released before cleanup")
            with pytest.raises(Busy, match="content lock held"):
                env.content.set_source_grants(
                    env.pv.source_id, (), expected_acl_revision=0, actor=OWNER
                )
        finally:
            release.set()
        assert response.result(timeout=3)[0] == 200
    env.content.set_source_grants(
        env.pv.source_id, (), expected_acl_revision=0, actor=OWNER
    )


def test_actual_loopback_job_to_search(tmp_path):
    env = setup(tmp_path)
    request_finished = Event()

    class CompletionServer(HTTPServer):
        def process_request(self, request, client_address):
            try:
                super().process_request(request, client_address)
            finally:
                request_finished.set()

    with CompletionServer(("127.0.0.1", 0), handler_for(env.app)) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with httpx.Client(
                base_url=f"http://127.0.0.1:{server.server_port}",
                trust_env=False,
                timeout=3,
            ) as client:

                def exchange(method, path, value=None, *, actor=OWNER, key=None):
                    headers = {"Authorization": "Bearer " + token(actor)}
                    if key:
                        headers["Idempotency-Key"] = key
                    request_finished.clear()
                    reply = client.request(method, path, json=value, headers=headers)
                    # Content-Length can finish the client read before the handler
                    # closes its ACL guard. Await actual server-side cleanup.
                    assert request_finished.wait(timeout=3), (
                        "HTTP request did not finish"
                    )
                    return reply.status_code, reply.json()

                exercise(env, exchange)
        finally:
            server.shutdown()
            thread.join(timeout=3)
            assert not thread.is_alive()


def test_index_cancel_before_dispatch_and_current_permissions(tmp_path):
    env = setup(tmp_path)
    env.controller.store.heartbeat()
    job = create(env)
    env.content.set_source_grants(
        env.pv.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    api(env, "POST", f"/v1/jobs/{job['job_id']}/cancel", {}, actor=VIEWER, expected=403)
    api(env, "POST", f"/v1/jobs/{job['job_id']}/cancel", {}, expected=202)
    with _executor(env.settings) as worker:
        worker.step()
        assert env.controller.store.get(job["job_id"]).status == "cancelled"
        assert env.index._active()[1] is None


def test_index_cancel_running_preserves_last_generation(tmp_path):
    env = setup(tmp_path)
    env.index.build(env.spec.selection, actor=OWNER)
    active = env.index.files.read("active.json")
    env.controller.store.heartbeat()
    job = create(env)
    child = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "tests.index_cancel_probe",
            "--root",
            str(env.settings.root),
            "--job",
            job["job_id"],
        ]
    )
    try:
        until = time.monotonic() + 12
        marker = env.settings.root / "cancel-ready"
        while not marker.exists():
            assert child.poll() is None
            assert time.monotonic() < until
            time.sleep(0.03)
        pid = int(marker.read_text())
        # API restart does not dispatch or mutate the running job.
        reopened = Controller(env.settings)
        assert reopened.get(OWNER, job["job_id"]).status == "running"
        reopened.cancel(OWNER, job["job_id"])
        child.wait(timeout=8)
        assert child.returncode == 0
        current = reopened.get(OWNER, job["job_id"])
        assert current.status == "cancelled" and not current.cancellable
        assert not Path(f"/proc/{pid}").exists()
        assert env.index.files.read("active.json") == active
        assert not (env.settings.root / "quarantine").exists()
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=5)
