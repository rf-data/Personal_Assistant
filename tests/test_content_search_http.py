"""Real verified synthetic bundles/FTS5/gateway, no real material or services."""

import http.client
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.content_store.adapters import (
    import_verified_bundle,
    verify_material_bundle,
    verify_srt_bundle,
)
from src.content_store.errors import Busy
from src.content_store.models import SourceGrant, canonical, sha256
from src.content_store.read_models import ContentReadSettings
from src.content_store.search_http import SearchReply, load_search_settings
from src.content_store.search_models import (
    SearchCapabilities,
    SearchRequest,
    SearchSettings,
)
from src.content_store.store import ContentStore
from src.job_control.controller import Controller
from src.job_control.http import Application
from src.job_control.models import Identity, Settings
from src.tools_rag import content_index
from src.tools_rag.content_index import ContentIndex
from src.tools_rag.content_index_models import IndexSelection, SearchResultPage
from tests.content_adapter_support import material, srt
from tests.content_store_support import OTHER, OWNER, VIEWER
from tests.test_content_fts import inventory, keyfile, make_index

ROUTE = "/v1/content/search"
TEXT = '# 😀 e\u0301 hello\r\n\tprint("hello")\r\nanswer = "hello"\n'


def token(actor):
    return "synthetic_search_token_" + actor.subject + "_000000000000"


def application(env, *, enabled=True, actors=(OWNER, VIEWER, OTHER), jobs="jobs"):
    settings = Settings(
        root=env.tmp / jobs,
        identities=tuple(
            Identity(**a.model_dump(), token_sha256=sha256(token(a).encode()))
            for a in actors
        ),
    )
    return Application(
        Controller(settings),
        content_settings=env.content_settings,
        search_settings=env.search_settings if enabled else None,
    )


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    connect = socket.socket.connect

    def local_only(sock, address):
        assert isinstance(address, tuple) and address[0] == "127.0.0.1", (
            "external network forbidden"
        )
        return connect(sock, address)

    monkeypatch.setattr(socket.socket, "connect", local_only)


@pytest.fixture
def env(tmp_path):
    bundle, _ = material(tmp_path, "code", code_raw=TEXT.encode())
    store = ContentStore.initialize(tmp_path / "content")
    pv = import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="search"
    ).version
    key = keyfile(tmp_path)
    index = ContentIndex.initialize(store, tmp_path / "index", cursor_key_file=key)
    selection = IndexSelection(parsed_version_ids=(pv.parsed_version_id,))
    index.build(selection, actor=OWNER)
    e = SimpleNamespace(
        tmp=tmp_path,
        content=store,
        pv=pv,
        key=key,
        index=index,
        selection=selection,
        bundle=bundle,
        content_settings=ContentReadSettings(root=store.root, cursor_key_file=key),
        search_settings=SearchSettings(schema_version=1, index_root=index.root),
    )
    e.app = application(e)
    return e


def request(
    env,
    value=None,
    *,
    actor=OWNER,
    method="POST",
    route=ROUTE,
    app=None,
    raw=None,
    headers=None,
):
    if raw is None:
        raw = (
            canonical(
                value if value is not None else dict(schema_version=1, query="hello")
            )
            if method == "POST"
            else b""
        )
    reply = (app or env.app).request(
        method,
        route,
        headers if headers is not None else {"Authorization": "Bearer " + token(actor)},
        raw,
    )
    try:
        code, data, mime = reply
        assert mime == "application/json"
        return code, json.loads(data)
    finally:
        if hasattr(reply, "close"):
            reply.close()


def search(env, **changes):
    status, data = request(env, dict(schema_version=1, query="hello", **changes))
    assert status == 200, data
    return SearchResultPage.model_validate(data)


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"schema_version": 1.0},
        {"query": ""},
        {"query": "  "},
        {"query": "x" * 65},
        {"query": "x " * 9},
        {"query": "x" * 513},
        {"query": 3},
        {"query": "\ud800"},
        {"limit": 0},
        {"limit": 101},
        {"limit": True},
        {"limit": "2"},
        {"course_id": "unknown"},
        {"source_ids": []},
        {"source_ids": ["same", "same"]},
        {"source_ids": [str(x) for x in range(33)]},
        {"content_types": ["unknown"]},
        {"content_types": ["code", "code"]},
        {"cursor": "x"},
        {"cursor": "x" * 1601},
        {"sql": "select *"},
        {"index_root": "/private"},
        {"reviewer": "admin"},
    ],
)
def test_request_rejects_unsupported_inputs(changes):
    with pytest.raises((ValidationError, UnicodeError)):
        SearchRequest.model_validate(dict(schema_version=1, query="hello") | changes)
    with pytest.raises(ValidationError):
        SearchRequest.model_validate(dict(query="hello"))


def test_actual_projection_http_page_content_reads_and_restart(env):
    before, raw = inventory(env.content.root), inventory(env.bundle.workspace)
    caps = request(env, method="GET", route=ROUTE + "/capabilities")
    assert caps[0] == 200 and SearchCapabilities.model_validate(caps[1]).enabled
    first = search(env, limit=1)
    assert first.items and first.next_cursor
    pages, cursor = list(first.items), first.next_cursor
    while cursor:
        page = search(env, limit=1, cursor=cursor)
        pages.extend(page.items)
        cursor = page.next_cursor
    assert len(pages) == 3 and len({h.index_record_id for h in pages}) == 3
    blocks = env.content.list_content_blocks(
        env.pv.parsed_version_id, actor=OWNER
    ).items
    for hit in pages:
        block = next(b for b in blocks if b.block_id == hit.block_id)
        assert hit.excerpt.text == block.text[hit.excerpt.start : hit.excerpt.end]
        assert hit.anchor.text_sha256 == block.text_sha256
        assert (
            hit.source_id == env.pv.source_id
            and hit.source_version_id == env.pv.source_version_id
        )
        assert hit.parsed_version_id == env.pv.parsed_version_id
        assert (
            hit.locators[0].raw_reference.sha256
            == block.locators[0].raw_artifact_sha256
        )
        status, text = request(env, method="GET", route=hit.text_route)
        assert status == 200 and text["text"] == block.text
    assert "".join(b.text for b in blocks) == TEXT
    env.app = application(env)  # Reopen existing roots, never rebuild on read.
    assert search(env, limit=1) == first
    assert (
        inventory(env.content.root) == before and inventory(env.bundle.workspace) == raw
    )


def test_authentication_course_and_source_access(env):
    assert request(env, headers={})[0] == 401
    assert (
        request(env, headers={"Authorization": "Bearer invalid", "X-Role": "operator"})[
            0
        ]
        == 401
    )
    code, denied = request(env, actor=OTHER)
    assert code == 200 and not denied["items"]
    unknown = request(
        env, dict(schema_version=1, query="hello", source_ids=["unknown"]), actor=OTHER
    )
    foreign = request(
        env,
        dict(schema_version=1, query="hello", source_ids=[env.pv.source_id]),
        actor=OTHER,
    )
    assert unknown == foreign
    assert not search(env, course_id="cs50_ai").items
    scoped = OWNER.model_copy(update={"courses": ()})
    assert request(env, app=application(env, actors=(scoped,)), actor=scoped) == (
        403,
        {
            "schema_version": 1,
            "error": {"code": "search_scope_denied", "message": "search scope denied"},
        },
    )
    env.content.set_source_grants(
        env.pv.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert request(env, actor=VIEWER)[1]["items"]
    env.content.set_source_grants(
        env.pv.source_id, (), expected_acl_revision=1, actor=OWNER
    )
    assert not request(env, actor=VIEWER)[1]["items"]


def test_cursor_signature_actor_parameters_ttl_and_live_revision(env, monkeypatch):
    cursor = search(env, limit=1).next_cursor
    value = dict(schema_version=1, query="hello", limit=1, cursor=cursor)
    assert request(env, value, actor=VIEWER)[0] == 422
    for changes in [
        {"query": "print"},
        {"limit": 2},
        {"content_types": ["code"]},
        {"cursor": cursor[:-5] + "AAAAA"},
    ]:
        assert request(env, value | changes)[0] == 422
    with monkeypatch.context() as patch:
        now = time.time()
        patch.setattr(content_index.time, "time", lambda: now + 301)
        assert request(env, value)[0] == 422
    env.content.set_source_grants(
        env.pv.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert request(env, value)[0] == 409
    assert search(env).items


@pytest.mark.parametrize(
    "target,state",
    [
        ("parsed_versions", "quarantined"),
        ("parsed_versions", "tombstoned"),
        ("source_versions", "quarantined"),
    ],
)
def test_quarantined_or_tombstoned_version_is_fail_closed(env, target, state):
    vid = (
        env.pv.parsed_version_id
        if target == "parsed_versions"
        else env.pv.source_version_id
    )
    with env.content._maintenance(), env.content._connection(write=True) as db:
        db.execute(f"UPDATE {target} SET state=? WHERE id=?", (state, vid))
    code, value = request(env)
    assert code == 409 and value["error"]["code"] == "stale_index"
    assert not request(env, actor=OTHER)[1]["items"]


def test_guard_blocks_writer_until_delivery_and_always_closes(env):
    response = env.app.request(
        "POST",
        ROUTE,
        {"Authorization": "Bearer " + token(OWNER)},
        canonical(dict(schema_version=1, query="hello")),
    )
    assert isinstance(response, SearchReply) and response.status == 200
    try:
        with pytest.raises(Busy):
            env.content.set_source_grants(
                env.pv.source_id, (), expected_acl_revision=0, actor=OWNER
            )
    finally:
        response.close()
        response.close()  # Idempotent transport cleanup.
    env.content.set_source_grants(
        env.pv.source_id, (), expected_acl_revision=0, actor=OWNER
    )


@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"[]",
        b'{"schema_version":1,"query":"hello","query":"secret"}',
        b'{"schema_version":1,"query":NaN}',
        b"\xff",
        b"[" * 1100,
    ],
)
def test_malformed_json_is_redacted_without_internal_error(env, raw):
    code, data = request(env, raw=raw)
    assert code == 422 and set(data) == {"schema_version", "error"}
    assert str(env.tmp) not in json.dumps(data)
    assert search(env).items  # No retained query slot/DB guard on errors.


def test_disabled_missing_generation_unknown_schema_and_key_rotation(env):
    disabled = application(env, enabled=False)
    assert request(env, app=disabled)[0] == 503
    assert not request(env, app=disabled, method="GET", route=ROUTE + "/capabilities")[
        1
    ]["enabled"]
    cursor = search(env, limit=1).next_cursor
    env.key.write_bytes(bytes(reversed(range(32))))
    assert (
        request(env, dict(schema_version=1, query="hello", limit=1, cursor=cursor))[0]
        == 422
    )
    identity = env.index.root / "identity.json"
    original = identity.read_bytes()
    identity.write_bytes(original.replace(b'"schema_version":1', b'"schema_version":2'))
    assert request(env)[0] == 503
    identity.write_bytes(original)
    (env.index.root / "active.json").unlink()  # Isolated synthetic index only.
    value = search(env)
    assert value.items == () and value.index_generation is None


def test_method_route_limits_and_fixed_errors(env, monkeypatch):
    assert request(env, method="GET")[0] == 405
    assert request(env, route=ROUTE + "/capabilities")[0] == 405
    assert request(env, route=ROUTE + "/anything")[0] == 404
    assert request(env, route=ROUTE + "?sql=select")[0] == 422
    assert request(env, raw=b"x" * 32769)[0] == 422

    def broken(*a, **kw):
        raise OSError("/private/credentials SQL secret")

    monkeypatch.setattr(ContentIndex, "_backend_spec", broken)
    code, data = request(env)
    assert code == 503 and data == {
        "schema_version": 1,
        "error": {"code": "unavailable", "message": "unavailable"},
    }


def test_foreign_partition_never_changes_visible_scores_or_leaks_errors(env):
    env.content.set_source_grants(
        env.pv.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    before = request(env, actor=VIEWER)[1]
    directory = env.tmp / "foreign"
    directory.mkdir()
    bundle, _ = srt(directory)
    foreign = import_verified_bundle(
        env.content, verify_srt_bundle(bundle), actor=OWNER, request_key="foreign"
    ).version
    env.index.build(
        IndexSelection(
            parsed_version_ids=tuple(
                sorted([env.pv.parsed_version_id, foreign.parsed_version_id])
            )
        ),
        actor=OWNER,
    )
    after = request(env, actor=VIEWER)[1]
    assert [
        {k: v for k, v in h.items() if k != "index_generation"} for h in before["items"]
    ] == [
        {k: v for k, v in h.items() if k != "index_generation"} for h in after["items"]
    ]
    _, active, manifest = env.index._active()
    proof = next(f for f in manifest.files if f.source_id == foreign.source_id)
    (
        env.index.root
        / "generations"
        / active.generation_id.split(":")[1]
        / active.build_id
        / proof.name
    ).write_bytes(b"private corrupt index")
    assert request(env, actor=VIEWER)[1] == after
    assert foreign.source_id not in json.dumps(after)
    assert request(env)[0] == 503


def test_settings_and_cli_require_explicit_separate_roots(env):
    for root in (env.content.root, env.tmp / "jobs", env.content.root / "nested"):
        with pytest.raises(ValueError):
            Application(
                env.app.controller,
                content_settings=env.content_settings,
                search_settings=SearchSettings(schema_version=1, index_root=root),
            )
    with pytest.raises(ValueError):
        Application(env.app.controller, search_settings=env.search_settings)
    cfg = env.tmp / "search.json"
    cfg.write_bytes(canonical(env.search_settings.model_dump(mode="json")))
    cfg.chmod(0o600)
    assert load_search_settings(cfg) == env.search_settings
    from scripts.job_control import main

    with pytest.raises(SystemExit) as error:
        main(["api", "--config", "unused", "--search-config", str(cfg)])
    assert error.value.code == 2


@pytest.mark.parametrize(
    "kind,query", [("html", "hello"), ("pdf", "print"), ("srt", "Hallo")]
)
def test_existing_format_locators_over_http(tmp_path, kind, query):
    index, store, pv, _, _, _, key = make_index(tmp_path, kind)
    env = SimpleNamespace(
        tmp=tmp_path,
        content_settings=ContentReadSettings(root=store.root, cursor_key_file=key),
        search_settings=SearchSettings(schema_version=1, index_root=index.root),
    )
    env.app = application(env)
    code, page = request(env, dict(schema_version=1, query=query))
    assert code == 200 and page["items"]
    if kind == "srt":
        assert page["items"][0]["locators"][0]["time_status"] == "known"
    elif kind == "pdf":
        assert page["items"][0]["locators"][0]["page"] is not None


def test_real_local_http_server_and_process_restart(env):
    config = env.tmp / "configuration"
    config.mkdir(mode=0o700)
    files = {
        "jobs": env.app.controller.settings,
        "content": env.content_settings,
        "search": env.search_settings,
    }
    for name, model in files.items():
        path = config / (name + ".json")
        path.write_bytes(canonical(model.model_dump(mode="json")))
        path.chmod(0o600)

    def exchange(port, path, body=None, auth=True):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        try:
            headers = {"Content-Type": "application/json"}
            if auth:
                headers["Authorization"] = "Bearer " + token(OWNER)
            connection.request(
                "POST" if body is not None else "GET", path, body, headers
            )
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    responses = []
    for _ in range(2):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        args = [
            sys.executable,
            "-m",
            "scripts.job_control",
            "api",
            "--config",
            str(config / "jobs.json"),
            "--content-config",
            str(config / "content.json"),
            "--search-config",
            str(config / "search.json"),
            "--port",
            str(port),
        ]
        with subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        ) as process:
            try:
                until = time.monotonic() + 10
                while True:
                    try:
                        status, _, raw = exchange(port, ROUTE + "/capabilities")
                        assert status == 200 and json.loads(raw)["enabled"]
                        break
                    except ConnectionRefusedError:
                        assert process.poll() is None, process.communicate()
                        assert time.monotonic() < until
                        time.sleep(0.05)
                status, headers, raw = exchange(
                    port, ROUTE, canonical(dict(schema_version=1, query="hello"))
                )
                assert status == 200 and headers["Cache-Control"] == "no-store"
                responses.append(SearchResultPage.model_validate_json(raw))
                assert exchange(port, ROUTE + "/capabilities", auth=False)[0] == 401
                assert exchange(port, ROUTE, b"{")[0] == 422
                # Writer can proceed after HTTP delivery: guard is closed by handler.
                with (
                    env.content._maintenance(),
                    env.content._connection(write=True) as db,
                ):
                    assert db.execute("SELECT 1").fetchone()[0] == 1
            finally:
                process.terminate()
                process.wait(timeout=5)
    assert responses[0] == responses[1] and len(responses[0].items) == 3


def test_generation_change_and_resource_limits_remain_fail_closed(env, monkeypatch):
    value = dict(
        schema_version=1,
        query="hello",
        limit=1,
        cursor=search(env, limit=1).next_cursor,
    )
    env.index.build(IndexSelection(parsed_version_ids=()), actor=OWNER)
    assert request(env, value)[0] == 409
    env.index.build(env.selection, actor=OWNER)
    with monkeypatch.context() as patch:
        patch.setattr(content_index, "MAX_MATCHES", 1)
        assert request(env)[1]["error"]["code"] == "query_too_broad"
    assert content_index.SLOTS.acquire(blocking=False)
    assert content_index.SLOTS.acquire(blocking=False)
    try:
        assert request(env)[1]["error"]["code"] == "busy"
    finally:
        content_index.SLOTS.release()
        content_index.SLOTS.release()
    assert search(env).items


@pytest.mark.parametrize("failure", ["disconnect", "expired", "serialize_timeout"])
def test_transport_failure_releases_guard_without_delivering_stale_bytes(
    env, failure, monkeypatch
):
    import io
    from email.message import Message

    from src.job_control.http import handler_for

    request_bytes = canonical(dict(schema_version=1, query="hello"))
    handler = object.__new__(handler_for(env.app))
    handler.command, handler.path = "POST", ROUTE
    handler.headers = Message()
    for key, value in {
        "Authorization": "Bearer " + token(OWNER),
        "Content-Type": "application/json",
        "Content-Length": str(len(request_bytes)),
    }.items():
        handler.headers[key] = value
    handler.rfile, handler.wfile = io.BytesIO(request_bytes), io.BytesIO()
    handler.connection = SimpleNamespace(settimeout=lambda value: None)
    if failure == "serialize_timeout":
        from src.content_store import search_http

        clock = time.monotonic
        offset = [0]
        encode = search_http.canonical

        def slow_encode(value):
            data = encode(value)
            if isinstance(value, dict) and "items" in value:
                offset[0] = 3
            return data

        monkeypatch.setattr(search_http, "canonical", slow_encode)
        monkeypatch.setattr(time, "monotonic", lambda: clock() + offset[0])
        handler.send_response = lambda status: pytest.fail(
            "serialization exhausted delivery budget"
        )
    elif failure == "expired":
        original = env.app.request

        def expired(*args, **kwargs):
            response = original(*args, **kwargs)
            response.deadline = -1
            return response

        env.app.request = expired
        handler.send_response = lambda status: pytest.fail(
            "expired response headers must not be sent"
        )
    else:

        def disconnected(status):
            raise BrokenPipeError("synthetic client disconnected")

        handler.send_response = disconnected
    handler.handle_request()
    assert not handler.wfile.getvalue()
    with env.content._maintenance(), env.content._connection(write=True) as db:
        assert db.execute("SELECT 1").fetchone()[0] == 1
