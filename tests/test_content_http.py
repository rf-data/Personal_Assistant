"""Actual loopback HTTP and B-adapter publication, no external networking."""

import http.client
import io
import json
import os
import socket
import threading
from http.server import HTTPServer
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from pydantic import ValidationError

from src.content_store.adapters import (
    import_verified_bundle,
    verify_material_bundle,
    verify_srt_bundle,
)
from src.content_store.errors import Busy, IntegrityError
from src.content_store.models import SourceGrant, SourceRegistration, sha256
from src.content_store.read_models import (
    ContentPage,
    ContentReadSettings,
    ParsedDTO,
    StructureDTO,
    TextWindow,
)
from src.content_store.read_views import route
from src.content_store.reader import ContentReader, load_content_settings
from src.content_store.store import ContentStore
from src.job_control.controller import Controller
from src.job_control.http import Application, handler_for
from src.job_control.models import Identity, Settings
from tests.content_adapter_support import attest, dump, material, srt
from tests.content_store_support import OTHER, OWNER

TOKENS = {
    name: "synthetic_content_" + name + "_" * 32
    for name in ("owner", "viewer", "other", "foreign")
}


@pytest.fixture
def scope(tmp_path, monkeypatch):
    store = ContentStore.initialize(tmp_path / "content")
    key = tmp_path / "cursor.key"
    key.write_bytes(b"synthetic-cursor-signing-key-v1!!!")
    key.chmod(0o600)
    settings = ContentReadSettings(root=store.root, cursor_key_file=key)
    identities = tuple(
        Identity(
            subject=name,
            role="viewer" if name in {"viewer", "foreign"} else "operator",
            courses=("cs50x" if name == "foreign" else "cs50_python",),
            token_sha256=sha256(token.encode()),
        )
        for name, token in TOKENS.items()
    )
    controller = Controller(Settings(root=tmp_path / "jobs", identities=identities))
    app = Application(controller, content_settings=settings)
    server = HTTPServer(("127.0.0.1", 0), handler_for(app))
    connect = socket.socket.connect
    dns = socket.getaddrinfo

    def guarded(self, address):
        assert address == server.server_address, (
            "Only this task's loopback server is allowed"
        )
        return connect(self, address)

    def names(host, port, *args, **kw):
        assert host == "127.0.0.1" and port == server.server_port
        return dns(host, port, *args, **kw)

    monkeypatch.setattr(socket.socket, "connect", guarded)
    monkeypatch.setattr(socket, "getaddrinfo", names)
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    )
    thread.start()
    result = SimpleNamespace(
        store=store, app=app, server=server, settings=settings, tmp=tmp_path
    )
    yield result
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)
    assert not thread.is_alive()


def get(scope, path, *, actor="owner", method="GET", body=None):
    connection = http.client.HTTPConnection(
        "127.0.0.1", scope.server.server_port, timeout=5
    )
    headers = {"Authorization": "Bearer " + TOKENS[actor]} if actor else {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    data = response.read()
    status = response.status
    headers = dict(response.getheaders())
    connection.close()
    return status, data, headers


def value(scope, path, **kw):
    status, data, _ = get(scope, path, **kw)
    return status, json.loads(data)


def publish(scope, kind="html", label="input", revision=None):
    bundle, doc = (
        srt(scope.tmp / label) if kind == "srt" else material(scope.tmp / label, kind)
    )
    if revision:
        attest(bundle, revision=revision)
    candidate = (
        verify_srt_bundle(bundle) if kind == "srt" else verify_material_bundle(bundle)
    )
    result = import_verified_bundle(
        scope.store, candidate, actor=OWNER, request_key=label
    )
    return bundle, doc, result.version


def pages(scope, path, *, limit=2, actor="owner"):
    found = []
    cursor = None
    while True:
        query = dict(limit=str(limit))
        if cursor:
            query["cursor"] = cursor
        status, data = value(scope, path + "?" + urlencode(query), actor=actor)
        assert status == 200, data
        ContentPage.model_validate(data)
        found.extend(data["items"])
        cursor = data["next_cursor"]
        if not cursor:
            return found


def test_http_e2e_after_restart_and_legacy_contract(scope):
    bundle, doc, v = publish(scope)

    def snapshot():
        return {
            str(p): (sha256(p.read_bytes()), p.stat().st_mode)
            for root in (scope.store.root, bundle.workspace)
            for p in root.rglob("*")
            if p.is_file()
        }

    before = snapshot()
    scope.app.content.reader = ContentReader(scope.settings)
    status, cap = value(scope, "/v1/content/capabilities")
    assert (
        status == 200 and cap["enabled"] and cap["capabilities"] == ["content_read_v1"]
    )
    assert value(scope, "/v1/content/capabilities", actor=None)[0] == 401
    source = route("sources", v.source_id)
    assert value(scope, source)[1]["course_id"] == "cs50_python"
    assert pages(scope, "/v1/content/sources")[0]["source_id"] == v.source_id
    versions = pages(scope, source + "/versions")
    assert versions[0]["source_version_id"] == v.source_version_id
    refs = pages(scope, versions[0]["parsed_versions_route"])
    assert refs == [
        dict(
            parsed_version_id=v.parsed_version_id,
            route=route("parsed", v.parsed_version_id),
        )
    ]
    status, parsed = value(scope, refs[0]["route"])
    assert status == 200
    ParsedDTO.model_validate(parsed)
    assert parsed["payload_sha256"] == sha256(bundle.normalized_path.read_bytes())
    assert parsed["block_count"] == len(doc.blocks)
    blocks = pages(scope, parsed["blocks_route"])
    internal = scope.store.list_content_blocks(
        v.parsed_version_id, actor=OWNER, limit=100
    ).items
    assert [b["aggregation_role"] for b in blocks] == [
        b.aggregation_role for b in internal
    ]
    assert [b["block_id"] for b in blocks] == [b.block_id for b in doc.blocks]
    for b, original in zip(blocks, doc.blocks, strict=True):
        status, window = value(scope, b["text_route"])
        assert status == 200 and TextWindow.model_validate(window).text == original.text
        assert (
            b["locators"][0]["raw_reference"]["source_version_id"]
            == v.source_version_id
        )
    raw = versions[0]["artifacts"][0]
    status, data, headers = get(scope, raw["download_route"])
    assert status == 200 and data == bundle.raw_path.read_bytes()
    assert headers["Content-Disposition"].startswith("attachment;")
    assert (
        headers["X-Content-Type-Options"] == "nosniff"
        and headers["Cache-Control"] == "no-store"
    )
    assert (
        headers["Content-Type"] == "application/octet-stream"
    )  # HTML never active inline.
    # Existing endpoints and envelopes do not acquire a content field/schema.
    assert "content" not in value(scope, "/v1/capabilities")[1]
    assert value(scope, "/v1/jobs") == (200, [])
    assert value(scope, "/v1/workflows/capabilities")[0] == 200
    all_bytes = json.dumps([parsed, blocks, versions]).encode()
    for private in (
        str(scope.tmp).encode(),
        b"store_key",
        b"source_file",
        b"token_sha256",
        b"implementation_path",
    ):
        assert private not in all_bytes
    assert snapshot() == before


@pytest.mark.parametrize("kind", ["pdf", "code", "srt"])
def test_content_types_time_geometry_and_structures(scope, kind):
    bundle, doc, v = publish(scope, kind)
    blocks = pages(scope, route("parsed", v.parsed_version_id, "blocks"))
    assert blocks
    for b in blocks:
        status, data, headers = get(scope, b["structure_route"])
        assert status == 200 and headers["Content-Disposition"].startswith(
            "attachment;"
        )
        structure = StructureDTO.model_validate_json(data)
        assert structure.block_id == b["block_id"]
        if kind == "pdf":
            assert b["locators"][0]["page"] == 1
            assert b["locators"][0]["bbox"] == [0, 0, 100, 100]
            if b["type"] == "code":
                assert structure.data["line_numbers"][0]["number"] == 1
                assert structure.data["code_view"] == "x = 1\nprint(x)\n# Ä"
        if kind == "srt":
            assert b["locators"][0]["time_status"] == "known"
            assert (
                value(scope, b["text_route"])[1]["text"]
                == doc.segments[b["order"]].text
            )
    if kind == "pdf":
        assert {b["type"] for b in blocks} == {"code", "table", "formula"}
    if kind == "code":
        assert (
            "".join(b["text"] for b in blocks) == bundle.raw_path.read_bytes().decode()
        )


@pytest.mark.parametrize("actor", ["viewer", "other", "foreign"])
def test_foreign_unknown_equal_and_sha_does_not_authorize(scope, actor):
    _, _, v = publish(scope)
    assert value(scope, "/v1/content/sources", actor=actor)[1]["items"] == []
    known = get(scope, route("sources", v.source_id), actor=actor)
    unknown = get(scope, route("sources", "resource:unknown"), actor=actor)
    assert known[:2] == unknown[:2] and known[0] == 404
    assert value(scope, route("parsed", v.parsed_version_id), actor=actor)[0] == 404
    sv = pages(scope, route("sources", v.source_id, "versions"))[0]
    assert get(scope, sv["artifacts"][0]["download_route"], actor=actor)[0] == 404


def test_grants_scope_and_revocation_between_pages(scope):
    _, _, v = publish(scope)
    scope.store.set_source_grants(
        v.source_id,
        (SourceGrant(subject="viewer"),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert value(scope, route("sources", v.source_id), actor="viewer")[0] == 200
    path = route("parsed", v.parsed_version_id, "blocks")
    status, page = value(scope, path + "?limit=1", actor="viewer")
    assert status == 200 and page["next_cursor"]
    scope.store.set_source_grants(v.source_id, (), expected_acl_revision=1, actor=OWNER)
    status, error = value(
        scope,
        path + "?" + urlencode(dict(limit=1, cursor=page["next_cursor"])),
        actor="viewer",
    )
    assert status == 409 and error["error"]["code"] == "snapshot_changed"
    assert value(scope, path, actor="viewer")[0] == 404
    # Even ownership does not override the authenticated course list.
    controller = scope.app.controller
    owner = controller.settings.identities[0].model_copy(update={"courses": ("cs50x",)})
    controller.settings = controller.settings.model_copy(
        update={"identities": (owner, *controller.settings.identities[1:])}
    )
    assert value(scope, route("sources", v.source_id))[0] == 404


@pytest.mark.parametrize("change", ["signature", "actor", "filter", "source_revision"])
def test_cursors_are_bound_and_snapshot_changes(scope, change):
    _, _, v = publish(scope)
    publish(scope, "code", "second")
    path = "/v1/content/sources"
    first = value(scope, path + "?limit=1")[1]
    cursor = first["next_cursor"]
    assert cursor
    query = dict(limit="1", cursor=cursor)
    actor = "owner"
    if change == "signature":
        query["cursor"] = cursor[:-1] + ("A" if cursor[-1] != "A" else "B")
    elif change == "actor":
        actor = "other"
    elif change == "filter":
        query["course_id"] = "cs50_python"
    else:
        publish(scope, "srt", "third")
    status, error = value(scope, path + "?" + urlencode(query), actor=actor)
    assert status == (409 if change == "source_revision" else 400)
    assert error["error"]["code"] in {"invalid_cursor", "snapshot_changed"}


def test_keysets_versions_refs_and_filter_before_pagination(scope):
    _, _, first = publish(scope)
    publish(scope, "html", "newparser", revision="b" * 40)
    publish(scope, "code", "other")
    sources = pages(scope, "/v1/content/sources", limit=1)
    assert [s["source_id"] for s in sources] == sorted(s["source_id"] for s in sources)
    assert len(sources) == 2
    assert value(scope, "/v1/content/sources?course_id=cs50x")[1]["items"] == []
    versions = pages(scope, route("sources", first.source_id, "versions"), limit=1)
    refs = pages(scope, versions[0]["parsed_versions_route"], limit=1)
    assert len(refs) == 2 and [r["parsed_version_id"] for r in refs] == sorted(
        r["parsed_version_id"] for r in refs
    )


@pytest.mark.parametrize(
    "state", ["quarantine", "source_tombstone", "parsed_tombstone"]
)
def test_hidden_states(scope, state):
    _, _, v = publish(scope)
    if state == "quarantine":
        (scope.store.root / v.payload.store_key).write_bytes(b"damaged")
        scope.store.verify_integrity(actor=OWNER)
    else:
        with scope.store._connection(write=True) as db:
            table, id_ = (
                ("sources", v.source_id)
                if state == "source_tombstone"
                else ("parsed_versions", v.parsed_version_id)
            )
            db.execute(f"UPDATE {table} SET state='tombstoned' WHERE id=?", (id_,))
            db.execute(
                "UPDATE metadata SET collection_revision=collection_revision+1 WHERE id=1"
            )
    assert value(scope, route("parsed", v.parsed_version_id))[0] == 404
    assert value(scope, route("parsed", v.parsed_version_id, "blocks"))[0] == 404


@pytest.mark.parametrize("damage", ["hash", "missing"])
def test_download_integrity_and_no_path_errors(scope, damage):
    bundle, _, v = publish(scope)
    raw = pages(scope, route("sources", v.source_id, "versions"))[0]["artifacts"][0]
    blob = scope.store.root / "blobs/sha256" / raw["sha256"][:2] / raw["sha256"]
    if damage == "missing":
        blob.unlink()
    else:
        blob.write_bytes(b"wrong")
    status, data, _ = get(scope, raw["download_route"])
    assert status == 503 and str(scope.tmp).encode() not in data
    assert bundle.raw_path.exists()


@pytest.mark.parametrize(
    "suffix",
    ["%2fetc", "%252fetc", "..", "%2E%2e", "%5Cetc", "%ZZ", "source%00", "%E2%98%83"],
)
def test_strict_single_decoding(scope, suffix):
    assert value(scope, "/v1/content/sources/" + suffix)[0] == 400


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "limit=-1",
        "limit=",
        "limit=1&limit=2",
        "offset=1",
        "schema_version=2",
        "cursor=bad",
        "course_id=wrong",
    ],
)
def test_invalid_queries_and_no_writes(scope, query):
    assert value(scope, "/v1/content/sources?" + query)[0] == 400
    assert value(scope, "/v1/content/sources", method="POST", body=b"{}")[0] == 405
    assert value(scope, "/v1/content/sources", body=b"{}")[0] == 422


def test_unconfigured_store_and_config_contract(scope):
    scope.app.content.settings = None
    scope.app.content.reader = None
    assert value(scope, "/v1/content/capabilities")[1]["enabled"] is False
    assert value(scope, "/v1/content/sources")[0] == 503
    scope.app.content.settings = scope.settings.model_copy(
        update={"root": scope.tmp / "absent"}
    )
    assert value(scope, "/v1/content/capabilities")[1]["capabilities"] == []
    assert not (scope.tmp / "absent").exists()
    with pytest.raises(ValidationError):
        ContentReadSettings.model_validate(
            dict(
                schema_version=2,
                root=str(scope.store.root),
                cursor_key_file=str(scope.settings.cursor_key_file),
            )
        )
    config = scope.tmp / "content-config.json"
    dump(config, scope.settings.model_dump(mode="json"))
    config.chmod(0o600)
    assert load_content_settings(config) == scope.settings
    scope.settings.cursor_key_file.chmod(0o644)
    with pytest.raises(IntegrityError):
        ContentReader(scope.settings)


def test_download_holds_acl_lock_through_same_handle(scope):
    _, _, v = publish(scope)
    sv = scope.store.list_source_versions(v.source_id, actor=OWNER)[0]
    reader = ContentReader(scope.settings)
    download = reader.download(v.source_id, sv.source_version_id, "primary", 0, OWNER)
    try:
        inode = os.fstat(download.stream.fileno()).st_ino
        with pytest.raises(Busy):
            scope.store.set_source_grants(
                v.source_id, (), expected_acl_revision=0, actor=OWNER
            )
        data = download.stream.read()
        assert sha256(data) == sv.manifest.artifacts[0].sha256
        assert os.fstat(download.stream.fileno()).st_ino == inode
    finally:
        download.close()
    scope.store.set_source_grants(v.source_id, (), expected_acl_revision=0, actor=OWNER)


def test_large_unicode_text_windows_and_private_metadata(scope):
    from src.tools_materials.parse_code import parse_code

    bundle, doc = material(scope.tmp / "large", kind="code")
    raw = ('# é😀\r\nprint("' + "Ä😀" * 20000 + '")\r\n').encode()
    bundle.raw_path.write_bytes(raw)
    doc, _ = parse_code(doc.binding, raw, doc.parser)
    target = (
        bundle.raw_path.parent.parent
        / doc.document_id.split(":")[1]
        / "normalized.v1.json"
    )
    data = doc.model_dump(mode="json")
    data["blocks"][-1]["data"]["private_path"] = "/home/private/secret-key"
    data["blocks"][-1]["data"]["arbitrary"] = {"token": "never-publish-free-metadata"}
    dump(target, data)
    bundle = bundle.model_copy(update={"normalized_path": target})
    receipt = json.loads(bundle.receipt_path.read_bytes())
    receipt.update(
        raw_sha256=sha256(raw),
        normalized_path=target.relative_to(bundle.workspace).as_posix(),
        normalized_sha256=sha256(target.read_bytes()),
    )
    dump(bundle.receipt_path, receipt)
    attest(bundle)
    v = import_verified_bundle(
        scope.store, verify_material_bundle(bundle), actor=OWNER, request_key="large"
    ).version
    block = max(
        pages(scope, route("parsed", v.parsed_version_id, "blocks")),
        key=lambda b: b["text_length"],
    )
    assert block["text"] is None and block["text_length"] == len(doc.blocks[-1].text)
    text = ""
    start = 0
    while start < block["text_length"]:
        status, window = value(
            scope, block["text_route"] + "?" + urlencode(dict(start=start, limit=16384))
        )
        assert status == 200 and window["start"] == start
        text += window["text"]
        start = window["end"]
    assert text == doc.blocks[-1].text and sha256(text.encode()) == block["text_sha256"]
    assert value(scope, block["text_route"] + "?limit=16385")[0] == 400
    assert value(scope, block["text_route"] + "?start=999999999")[0] == 400
    status, data, headers = get(scope, block["structure_route"])
    assert status == 200 and json.loads(data)["redacted"]
    assert b"secret-key" not in data and b"never-publish" not in data
    assert headers["Content-Type"] == "application/json"


def test_shared_blob_still_requires_source_scope(scope):
    bundle, _, v = publish(scope)
    source = scope.store.register_source(
        SourceRegistration(
            identity_namespace="synthetic",
            external_identity="other-source",
            course_id="cs50_python",
            source_type="synthetic",
            source_origin="synthetic",
        ),
        actor=OTHER,
    )
    raw = bundle.raw_path.read_bytes()
    scope.store.store_raw_artifact(
        source.source_id,
        io.BytesIO(raw),
        expected_sha256=sha256(raw),
        expected_size=len(raw),
        mime_type="text/html",
        actor=OTHER,
    )
    assert value(scope, route("sources", source.source_id), actor="other")[0] == 200
    assert value(scope, route("sources", v.source_id), actor="other")[0] == 404
    original = pages(scope, route("sources", v.source_id, "versions"))[0]["artifacts"][
        0
    ]
    assert get(scope, original["download_route"], actor="other")[0] == 404


def test_existing_c20_html_workflow_over_actual_http(scope):
    from scripts.cs50_workflow_demo import inputs
    from src.workflows.http_models import WorkflowInspection

    entry = inputs(scope.tmp / "workflow-inputs")
    controller = scope.app.controller
    settings = controller.settings.model_copy(
        update={"catalog": {"workflow_source": entry}, "workflows_enabled": True}
    )
    scope.app.controller = Controller(settings)
    status, result = value(
        scope,
        "/v1/workflows/inspect",
        method="POST",
        body=json.dumps(
            dict(source_ref="workflow_source", workflow_id="synthetic_workflow")
        ).encode(),
    )
    assert status == 200, result
    view = WorkflowInspection.model_validate(result)
    assert view.current_job is None and len(view.workflow.stages) == 9
    assert scope.app.controller.store.all() == ()
    assert value(scope, "/v1/workflows/capabilities")[1]["enabled"]


def test_http_download_serializes_parallel_acl_change(scope, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    _, _, v = publish(scope)
    raw = pages(scope, route("sources", v.source_id, "versions"))[0]["artifacts"][0]
    reader = scope.app.content.reader
    download = reader.download
    opened = threading.Event()
    release = threading.Event()

    def held(*args, **kwargs):
        result = download(*args, **kwargs)
        opened.set()
        if not release.wait(4):
            result.close()
            raise TimeoutError
        return result

    monkeypatch.setattr(reader, "download", held)
    with ThreadPoolExecutor(max_workers=1) as pool:
        response = pool.submit(get, scope, raw["download_route"])
        try:
            assert opened.wait(4)
            with pytest.raises(Busy):
                scope.store.set_source_grants(
                    v.source_id, (), expected_acl_revision=0, actor=OWNER
                )
        finally:
            release.set()
        status, data, _ = response.result(timeout=5)
    assert status == 200 and sha256(data) == raw["sha256"]


def test_download_handle_is_sealed_and_survives_source_mutation(scope):
    import fcntl

    from src.content_store.read_files import GET_SEALS, SEAL_WRITE

    bundle, _, v = publish(scope)
    reader = ContentReader(scope.settings)
    download = reader.download(v.source_id, v.source_version_id, "primary", 0, OWNER)
    try:
        assert fcntl.fcntl(download.stream.fileno(), GET_SEALS) & SEAL_WRITE
        with pytest.raises(OSError):
            os.write(download.stream.fileno(), b"mutated")
        digest = sha256(bundle.raw_path.read_bytes())
        blob = scope.store.root / "blobs/sha256" / digest[:2] / digest
        blob.write_bytes(b"concurrent filesystem corruption")
        assert download.stream.read() == bundle.raw_path.read_bytes()
    finally:
        download.close()


def test_raw_roles_ordinals_and_cross_source_version_binding(scope):
    _, _, v = publish(scope)
    _, _, other = publish(scope, "code", "other")
    base = ("sources", v.source_id, "versions", v.source_version_id, "raw")
    assert get(scope, route(*base, "other", 0))[0] == 404
    assert get(scope, route(*base, "primary", 1))[0] == 404
    assert (
        get(
            scope,
            route(
                "sources",
                v.source_id,
                "versions",
                other.source_version_id,
                "raw",
                "primary",
                0,
            ),
        )[0]
        == 404
    )
