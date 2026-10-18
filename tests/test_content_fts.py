"""Actual SQLite/ContentStore integration, synthetic originals, no external services."""

import json
import os
import signal
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from src.content_store._testing import publish_synthetic, synthetic_content_index
from src.content_store.adapters import (
    import_verified_bundle,
    verify_material_bundle,
    verify_srt_bundle,
)
from src.content_store.errors import (
    Busy,
    Forbidden,
    IntegrityError,
    InvalidInput,
    NotFound,
    Unavailable,
)
from src.content_store.index_models import IndexProjectionConfig
from src.content_store.models import SourceGrant, sha256
from src.content_store.store import ContentStore
from src.job_control.models import Principal
from src.tools_rag import content_fts
from src.tools_rag.content_index import ContentIndex, RetrievalFault
from src.tools_rag.content_index_models import IndexSelection
from tests.content_adapter_support import material, srt
from tests.content_store_support import OTHER, OWNER, VIEWER, config, payload, seeded


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*a, **k):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


def keyfile(tmp_path):
    p = tmp_path / "cursor.key"
    p.write_bytes(bytes(range(32)))
    p.chmod(0o600)
    return p


def make_index(tmp_path, kind="code"):
    store = ContentStore.initialize(tmp_path / "content")
    if kind == "srt":
        b, doc = srt(tmp_path)
        candidate = verify_srt_bundle(b)
    else:
        b, doc = material(tmp_path, kind)
        candidate = verify_material_bundle(b)
    v = import_verified_bundle(
        store, candidate, actor=OWNER, request_key="first"
    ).version
    key = keyfile(tmp_path)
    index = ContentIndex.initialize(store, tmp_path / "index", cursor_key_file=key)
    selection = IndexSelection(parsed_version_ids=(v.parsed_version_id,))
    receipt = index.build(selection, actor=OWNER)
    return index, store, v, doc, selection, receipt, key


def hits(index, query="hello", **kw):
    with index.search_lexical(query, actor=kw.pop("actor", OWNER), **kw) as page:
        return page


def inventory(path):
    return {
        str(p.relative_to(path)): (p.stat().st_mode, sha256(p.read_bytes()))
        for p in path.rglob("*")
        if p.is_file()
    }


@pytest.mark.parametrize(
    "kind,query",
    [("code", "hello"), ("html", "functions"), ("pdf", "print"), ("srt", "Hallo")],
)
def test_actual_build_search_restart_provenance(tmp_path, kind, query):
    i, store, v, doc, sel, receipt, key = make_index(tmp_path, kind)
    before = inventory(store.root)
    page = hits(i, query)
    if kind == "html" and not page.items:
        page = hits(i, "hello")
    assert page.items
    again = hits(
        ContentIndex(ContentStore(store.root), i.root, cursor_key_file=key), query
    )
    assert again == hits(i, query)
    for hit in page.items:
        assert (
            hit.source_id == v.source_id
            and hit.parsed_version_id == v.parsed_version_id
        )
        assert (
            hit.method == "lexical" and hit.components[0].direction == "lower_is_better"
        )
        assert hit.ranking_score > 0 and hit.anchor.offset_unit == "unicode_codepoint"
        block = next(
            b
            for b in store.list_content_blocks(
                v.parsed_version_id, actor=OWNER, limit=100
            ).items
            if b.block_id == hit.block_id
        )
        assert hit.excerpt.text == block.text[hit.excerpt.start : hit.excerpt.end]
        assert hit.excerpt.text_sha256 == block.text_sha256
        assert str(tmp_path) not in hit.model_dump_json()
        assert (
            "receipt" not in hit.model_dump_json()
            and "owner" not in hit.model_dump_json()
        )
        if kind == "pdf":
            assert hit.content_type == "code" and "1  x" in hit.excerpt.text
        if kind == "srt":
            assert (
                hit.locators[0].time_status == "known"
                and hit.locators[0].start is not None
            )
    assert inventory(store.root) == before


def test_repeated_build_paging_filters_and_generation_switch(tmp_path):
    i, store, v, _, sel, r, key = make_index(tmp_path, "srt")
    with i.search_lexical("x", actor=OWNER, limit=1) as page:
        assert all(h.source_id == v.source_id for h in page.items)
    first = hits(i, "Hallo", limit=1)
    same = i.build(sel, actor=OWNER)
    assert (
        same.generation_id == r.generation_id
        and same.record_set_sha256 == r.record_set_sha256
    )
    assert hits(i, "Hallo", limit=1) == first
    assert not hits(i, "Hallo", source_ids=("foreign",)).items
    assert not hits(i, "Hallo", content_types=("code",)).items
    assert not hits(i, "Hallo", course_id="cs50_ai").items
    assert not hits(i, "nonexistentword").items
    assert i.inspect_builds(actor=OWNER)[0].state in {"active", "retired"}
    old = next(x for x in i.inspect_builds(actor=OWNER) if x.build_id == r.build_id)
    i.discard_build(old.build_id, actor=OWNER)
    assert hits(i, "Hallo").items
    with pytest.raises(InvalidInput):
        i.discard_build(same.build_id, actor=OWNER)


@pytest.mark.parametrize(
    "query", ["", "   ", "x" * 513, "x" * 65, " ".join(["x"] * 9), None, "\ud800"]
)
def test_query_limits(tmp_path, query):
    i, *_ = make_index(tmp_path)
    with pytest.raises(RetrievalFault, match="invalid_parameter"):
        hits(i, query)


@pytest.mark.parametrize(
    "query", ["*", '"', "()", ";", '" OR "x', "hello; DROP TABLE records", "x+y", "x-y"]
)
def test_operators_are_literal_and_bounded(tmp_path, query):
    i, *_ = make_index(tmp_path)
    assert isinstance(hits(i, query).items, tuple)
    assert hits(i, "hello").items


def test_acl_live_scope_revocation_and_foreign_counts(tmp_path):
    i, store, v, _, _, _, _ = make_index(tmp_path)
    assert hits(i, actor=OTHER).items == ()
    store.set_source_grants(
        v.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert hits(i, actor=VIEWER).items
    store.set_source_grants(v.source_id, (), expected_acl_revision=1, actor=OWNER)
    assert hits(i, actor=VIEWER).items == ()
    assert (
        hits(
            i, actor=Principal(subject=OWNER.subject, role="operator", courses=())
        ).items
        == ()
    )
    assert "total_count" not in hits(i).model_dump_json()
    with pytest.raises(Forbidden):
        hits(i, actor="owner")


@pytest.mark.parametrize("target", ["source", "sv", "parsed", "artifact"])
def test_current_tombstone_quarantine(tmp_path, target):
    i, store, v, *_ = make_index(tmp_path)
    statements = {
        "source": ("UPDATE sources SET state='tombstoned' WHERE id=?", v.source_id),
        "sv": (
            "UPDATE source_versions SET state='quarantined' WHERE id=?",
            v.source_version_id,
        ),
        "parsed": (
            "UPDATE parsed_versions SET state='tombstoned' WHERE id=?",
            v.parsed_version_id,
        ),
        "artifact": (
            "UPDATE artifacts SET state='quarantined' WHERE sha256=?",
            v.payload.sha256,
        ),
    }
    sql, arg = statements[target]
    with store._maintenance(), store._connection(write=True) as db:
        db.execute(sql, (arg,))
        db.execute("UPDATE metadata SET collection_revision=collection_revision+1")
    if target == "source":
        assert hits(i).items == ()
    else:
        with pytest.raises(RetrievalFault, match="stale_index"):
            hits(i)


def test_corrupt_index_schema_and_metadata(tmp_path):
    i, _, _, _, _, _, _ = make_index(tmp_path)
    _, active, m = i._active()
    proof = m.files[0]
    data = i.files.read(
        "generations/"
        + active.generation_id.split(":")[1]
        + "/"
        + active.build_id
        + "/"
        + proof.name
    )
    path = (
        i.root
        / "generations"
        / active.generation_id.split(":")[1]
        / active.build_id
        / proof.name
    )
    path.write_bytes(b"broken")
    with pytest.raises(Unavailable):
        hits(i)
    path.write_bytes(data)
    assert hits(i).items
    with sqlite3.connect(":memory:") as db:
        db.deserialize(data)
        db.execute("DELETE FROM fts")
        db.commit()
        broken = db.serialize()
    path.write_bytes(broken)
    with pytest.raises(Unavailable):
        hits(i)


def test_builder_failure_keeps_old_generation_and_busy(tmp_path, monkeypatch):
    i, _, _, _, sel, _, _ = make_index(tmp_path)
    before = hits(i)
    original = content_fts.build_database

    def fail(records, **kwargs):
        assert hits(i) == before  # real old generation readable during rebuild
        with pytest.raises(Busy):
            i.build(sel, actor=OWNER)
        original(records, **kwargs)
        raise OSError("injected disk failure")

    monkeypatch.setattr(content_fts, "build_database", fail)
    with pytest.raises(OSError):
        i.build(sel, actor=OWNER)
    assert hits(i) == before
    failed = next(r for r in i.inspect_builds(actor=OWNER) if r.state == "failed")
    i.discard_build(failed.build_id, actor=OWNER)


def synthetic_index(tmp_path, *, count=4):
    from src.content_store._testing import SyntheticPayload
    from src.content_store.models import ContentBlock

    store, _, ref, sv = seeded(tmp_path)
    base = json.loads(payload(ref.sha256))["blocks"][1]
    blocks = []
    for n in range(count):
        b = json.loads(json.dumps(base))
        b.update(
            block_id=f"synthetic-block:{n}",
            order=n,
            payload_pointer=f"/blocks/{n}",
            text=f"function Python café 😀 print {n}\n    x = x² + 1",
        )
        b["locators"][0].update(
            origin_pointer=f"/blocks/{n}", time_status="unknown", start=None, end=None
        )
        blocks.append(ContentBlock.model_validate(b))
    v = publish_synthetic(
        store,
        sv.source_version_id,
        SyntheticPayload(blocks=tuple(blocks)).model_dump_json().encode(),
        config(),
        actor=OWNER,
    ).version
    key = keyfile(tmp_path)
    i = synthetic_content_index(
        store, tmp_path / "index", cursor_key_file=key, initialize=True
    )
    sel = IndexSelection(parsed_version_ids=(v.parsed_version_id,))
    i.build(sel, actor=OWNER)
    return i, store, v, sel, key


def test_real_pagination_cursor_filters_actor_and_revision(tmp_path):
    i, store, v, sel, key = synthetic_index(tmp_path, count=5)
    page = hits(i, "function", limit=2)
    assert len(page.items) == 2 and page.next_cursor
    second = hits(i, "function", limit=2, cursor=page.next_cursor)
    third = hits(i, "function", limit=2, cursor=second.next_cursor)
    ids = [h.index_record_id for p in [page, second, third] for h in p.items]
    assert len(ids) == 5 and len(set(ids)) == 5 and third.next_cursor is None
    assert all(
        h.locators[0].start is None and h.locators[0].time_status == "unknown"
        for h in page.items
    )
    for kw in [
        dict(query="Python"),
        dict(actor=OTHER),
        dict(limit=1),
        dict(source_ids=(v.source_id,)),
    ]:
        query = kw.pop("query", "function")
        with pytest.raises(RetrievalFault, match="invalid_cursor"):
            hits(i, query, limit=kw.pop("limit", 2), cursor=page.next_cursor, **kw)
    for value in ["bad", page.next_cursor[:-1] + "x"]:
        with pytest.raises(RetrievalFault, match="invalid_cursor"):
            hits(i, "function", limit=2, cursor=value)
    store.set_source_grants(
        v.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    with pytest.raises(RetrievalFault, match="snapshot_changed"):
        hits(i, "function", limit=2, cursor=page.next_cursor)
    changed = IndexSelection(
        parsed_version_ids=(v.parsed_version_id,),
        config=IndexProjectionConfig(schema_version=1, max_codepoints=15),
    )
    fresh = hits(i, "function", limit=2)
    i.build(changed, actor=OWNER)
    with pytest.raises(RetrievalFault, match="snapshot_changed"):
        hits(i, "function", limit=2, cursor=fresh.next_cursor)


def test_source_stats_no_existence_leak_and_whole_partition_stale(tmp_path):
    i, store, v, sel, key = synthetic_index(tmp_path, count=4)
    before = hits(i, "function")
    # Same source but multiple pinned parser versions; one invalid version blocks the partition.
    v2 = publish_synthetic(
        store,
        v.source_version_id,
        payload(before.items[0].locators[0].raw_artifact_sha256, text="function"),
        config(implementation_revision="other"),
        actor=OWNER,
        request_key="second",
    ).version
    combined = IndexSelection(
        parsed_version_ids=tuple(sorted([v.parsed_version_id, v2.parsed_version_id]))
    )
    i.build(combined, actor=OWNER)
    with store._maintenance(), store._connection(write=True) as db:
        db.execute(
            "UPDATE parsed_versions SET state='quarantined' WHERE id=?",
            (v2.parsed_version_id,),
        )
    with pytest.raises(RetrievalFault, match="stale_index"):
        hits(i, "function")


@pytest.mark.parametrize("phase", ["ready", "published", "active"])
def test_process_kill_interrupted_build_never_activates(tmp_path, phase):
    i, _, _, _, sel, _, key = make_index(tmp_path)
    expected = hits(i)
    script = """
import os,signal,sys
from src.content_store.store import ContentStore
from src.tools_rag.content_index import ContentIndex
from src.tools_rag.content_index_models import IndexSelection
from tests.content_store_support import OWNER
index=ContentIndex(ContentStore(sys.argv[1]),sys.argv[2],cursor_key_file=sys.argv[3])
phase=sys.argv[5]
publish=index.files.publish
write=index.files.json
def stop(*args):
    if phase=='published':publish(*args)
    os.kill(os.getpid(),signal.SIGKILL)
def active(relative,*args,**kwargs):
    write(relative,*args,**kwargs)
    if relative=='active.json':os.kill(os.getpid(),signal.SIGKILL)
if phase=='active':index.files.json=active
else:index.files.publish=stop
index.build(IndexSelection(parsed_version_ids=(sys.argv[4],)),actor=OWNER)
"""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(i.store.root),
            str(i.root),
            str(key),
            sel.parsed_version_ids[0],
            phase,
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        timeout=30,
    )
    assert result.returncode == -signal.SIGKILL and hits(i) == expected
    if phase != "active":
        stopped = next(
            r for r in i.inspect_builds(actor=OWNER) if r.state == "interrupted"
        )
        i.discard_build(stopped.build_id, actor=OWNER)
    else:
        assert sum(r.state == "active" for r in i.inspect_builds(actor=OWNER)) == 1
    assert i.build(sel, actor=OWNER).state == "active"


def test_missing_fts5_empty_index_and_wrong_key_or_root(tmp_path, monkeypatch):
    i, _, _, _, sel, _, _ = make_index(tmp_path)
    assert i.build(IndexSelection(parsed_version_ids=()), actor=OWNER).record_count == 0
    assert hits(i).items == ()
    monkeypatch.setattr(
        content_fts,
        "expected_schema",
        lambda: (_ for _ in ()).throw(Unavailable("missing FTS5")),
    )
    with pytest.raises(Unavailable):
        i.build(sel, actor=OWNER)


def test_response_guard_and_large_match_limit(tmp_path, monkeypatch):
    i, store, v, sel, key = synthetic_index(tmp_path, count=4)
    with i.search_lexical("function", actor=OWNER) as page:
        assert page.items
        with pytest.raises(Busy):
            store.set_source_grants(
                v.source_id, (), expected_acl_revision=0, actor=OWNER
            )
        with pytest.raises(Busy):
            i.build(sel, actor=OWNER)
    from src.tools_rag import content_index as module

    monkeypatch.setattr(module, "MAX_MATCHES", 1)
    with pytest.raises(RetrievalFault, match="query_too_broad"):
        hits(i, "function")


def test_unicode_multiword_code_math_and_no_token_queries(tmp_path):
    i, *_ = synthetic_index(tmp_path)
    assert hits(i, "Python café").items
    assert not hits(i, "Python cafe").items  # diacritics retained
    assert hits(i, "FUNCTION").items  # Unicode61 case folding
    assert hits(i, "x²").items  # lexical token, no equivalence claim
    assert not hits(i, "😀").items
    assert all("\n    x" in h.excerpt.text for h in hits(i, "Python").items)


def test_foreign_partition_cannot_change_scores_or_report_corruption(tmp_path):
    from src.content_store._testing import register_synthetic_version
    from src.content_store.models import RawArtifact, RawManifest
    from tests.content_store_support import raw, registration

    i, store, v, sel, _ = synthetic_index(tmp_path)
    store.set_source_grants(
        v.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    before = hits(i, "function", actor=VIEWER)
    other = store.register_source(registration("private-other"), actor=OWNER)
    ref = raw(store, other.source_id)
    sv = register_synthetic_version(
        store,
        other.source_id,
        RawManifest(artifacts=(RawArtifact(**ref.model_dump()),)),
        actor=OWNER,
    )
    v2 = publish_synthetic(
        store,
        sv.source_version_id,
        payload(ref.sha256, text="function " * 50),
        config(),
        actor=OWNER,
        request_key="foreign",
    ).version
    i.build(
        IndexSelection(
            parsed_version_ids=tuple(
                sorted([v.parsed_version_id, v2.parsed_version_id])
            )
        ),
        actor=OWNER,
    )
    after = hits(i, "function", actor=VIEWER)
    assert [h.model_dump(exclude={"index_generation"}) for h in before.items] == [
        h.model_dump(exclude={"index_generation"}) for h in after.items
    ]
    _, active, manifest = i._active()
    proof = next(f for f in manifest.files if f.source_id == other.source_id)
    path = (
        i.root
        / "generations"
        / active.generation_id.split(":")[1]
        / active.build_id
        / proof.name
    )
    path.write_bytes(b"corrupt private partition")
    assert hits(i, "function", actor=VIEWER) == after
    assert other.source_id not in after.model_dump_json()
    with pytest.raises(Unavailable):
        hits(i, "function")


@pytest.mark.parametrize("mutation", ["schema", "metadata", "fts", "record"])
def test_backend_checks_actual_sqlite_contents_even_with_recomputed_file_hash(
    tmp_path, mutation
):
    import time

    i, _, _, _, sel, *_ = make_index(tmp_path)
    _, active, manifest = i._active()
    data = i.files.read(
        "generations/"
        + active.generation_id.split(":")[1]
        + "/"
        + active.build_id
        + "/"
        + manifest.files[0].name
    )
    with i.store._maintenance(), i.store._connection() as db:
        _, records, _, _ = i._export(db, sel, OWNER)
    changes = {
        "schema": "PRAGMA user_version=999",
        "metadata": "UPDATE metadata SET value='wrong' WHERE key='tokenizer'",
        "fts": "DELETE FROM fts",
        "record": "UPDATE records SET text='tampered'",
    }
    with sqlite3.connect(":memory:") as db:
        db.deserialize(data)
        db.execute(changes[mutation])
        db.commit()
        broken = db.serialize()
    assert sha256(broken) != sha256(data)
    with pytest.raises((Unavailable, IntegrityError)):
        content_fts.search_database(
            broken, records, '"hello"', None, time.monotonic() + 2
        )


def test_activation_failure_and_grant_change_during_build(tmp_path, monkeypatch):
    i, store, v, _, sel, first, _ = make_index(tmp_path)
    expected = hits(i)
    write = i.files.json

    def fail(relative, *a, **kw):
        if relative == "active.json":
            raise OSError("injected activation failure")
        return write(relative, *a, **kw)

    monkeypatch.setattr(i.files, "json", fail)
    with pytest.raises(Unavailable):
        i.build(sel, actor=OWNER)
    assert hits(i) == expected
    monkeypatch.setattr(i.files, "json", write)
    original = content_fts.build_database

    def revoke(records, **kwargs):
        store.set_source_grants(v.source_id, (), expected_acl_revision=0, actor=OWNER)
        return original(records, **kwargs)

    monkeypatch.setattr(content_fts, "build_database", revoke)
    with pytest.raises(Unavailable):
        i.build(sel, actor=OWNER)
    assert i._active()[1].build_id == first.build_id


def test_cursor_expiry_and_private_files(tmp_path, monkeypatch):
    from src.tools_rag import content_index as module

    i, _, _, _, key = synthetic_index(tmp_path)
    page = hits(i, "function", limit=1)
    now = module.time.time()
    monkeypatch.setattr(module.time, "time", lambda: now + 301)
    with pytest.raises(RetrievalFault, match="invalid_cursor"):
        hits(i, "function", limit=1, cursor=page.next_cursor)
    for p in i.root.rglob("*"):
        assert p.stat().st_mode & 0o077 == 0
    key.chmod(0o644)
    with pytest.raises((Unavailable, IntegrityError)):
        synthetic_content_index(i.store, i.root, cursor_key_file=key)


def test_cli_read_only_defaults_and_explicit_rebuild(tmp_path):
    i, store, v, _, _, _, key = make_index(tmp_path)
    argv = [sys.executable, "-m", "scripts.content_index"]
    common = [
        "--store",
        str(store.root),
        "--index",
        str(i.root),
        "--cursor-key",
        str(key),
        "--actor",
        OWNER.subject,
        "--role",
        OWNER.role,
        "--course",
        OWNER.courses[0],
    ]
    env = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": "/usr/lib/python3/dist-packages",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    before = inventory(store.root), inventory(i.root)
    for op in [
        ["build", "--version", v.parsed_version_id],
        ["search", "--query", "hello"],
        ["status"],
    ]:
        p = subprocess.run(
            argv + op + common, env=env, capture_output=True, text=True, timeout=30
        )
        assert p.returncode == 0, p.stderr
        assert str(tmp_path) not in p.stdout + p.stderr
        assert json.loads(p.stdout)
    assert (inventory(store.root), inventory(i.root)) == before
    p = subprocess.run(
        argv + ["build", "--execute", "--version", v.parsed_version_id] + common,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert p.returncode == 0 and json.loads(p.stdout)["state"] == "active"


def test_new_raw_version_explicit_selection_and_missing_version(tmp_path):
    from src.content_store._testing import register_synthetic_version
    from src.content_store.models import RawArtifact, RawManifest
    from tests.content_store_support import raw

    i, store, v, sel, _ = synthetic_index(tmp_path)
    old = hits(i, "function")
    ref = raw(store, v.source_id, b"new synthetic original")
    sv = register_synthetic_version(
        store,
        v.source_id,
        RawManifest(artifacts=(RawArtifact(**ref.model_dump()),)),
        actor=OWNER,
    )
    v2 = publish_synthetic(
        store,
        sv.source_version_id,
        payload(ref.sha256, text="replacement"),
        config(),
        actor=OWNER,
        request_key="new-raw-version",
    ).version
    assert (
        hits(i, "function").items == old.items
    )  # intentionally pinned, no invented latest
    i.build(IndexSelection(parsed_version_ids=(v2.parsed_version_id,)), actor=OWNER)
    assert not hits(i, "function").items
    assert all(
        h.source_version_id == sv.source_version_id
        for h in hits(i, "replacement").items
    )
    with pytest.raises(NotFound):
        i.build(IndexSelection(parsed_version_ids=("missing",)), actor=OWNER)


def test_unbuilt_index_status_is_read_only_and_schema_is_explicit(tmp_path):
    i, store, _, _, _, _, key = make_index(tmp_path)
    empty = ContentIndex.initialize(
        store, tmp_path / "empty-index", cursor_key_file=key
    )
    before = inventory(empty.root)
    assert empty.inspect_builds(actor=OWNER) == ()
    assert hits(empty).items == ()
    assert inventory(empty.root) == before
    for schema in [None, True, 2]:
        value = json.loads((i.root / "active.json").read_text())
        if schema is None:
            value.pop("schema_version")
        else:
            value["schema_version"] = schema
        (i.root / "active.json").write_text(json.dumps(value))
        with pytest.raises(Unavailable):
            hits(i)
        value["schema_version"] = 1
        (i.root / "active.json").write_text(json.dumps(value))


def test_overlapping_process_builds_and_reader(tmp_path):
    import selectors

    i, _, v, _, sel, _, key = make_index(tmp_path)
    expected = hits(i)
    script = """
import sys
from src.content_store.store import ContentStore
from src.tools_rag import content_fts
from src.tools_rag.content_index import ContentIndex
from src.tools_rag.content_index_models import IndexSelection
from tests.content_store_support import OWNER
original=content_fts.build_database
def pause(records,**kwargs):
    print('building',flush=True)
    sys.stdin.readline()
    return original(records,**kwargs)
content_fts.build_database=pause
i=ContentIndex(ContentStore(sys.argv[1]),sys.argv[2],cursor_key_file=sys.argv[3])
r=i.build(IndexSelection(parsed_version_ids=(sys.argv[4],)),actor=OWNER)
print(r.state,flush=True)
"""
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            script,
            str(i.store.root),
            str(i.root),
            str(key),
            v.parsed_version_id,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": "/usr/lib/python3/dist-packages",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            assert selector.select(timeout=30)
        assert child.stdout.readline().strip() == "building"
        assert hits(i) == expected
        with pytest.raises(Busy):
            i.build(sel, actor=OWNER)
        out, err = child.communicate("continue\n", timeout=30)
        assert child.returncode == 0 and out.strip() == "active", err
        assert hits(i) == expected
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)


def test_query_deadline_capacity_filters_and_file_safety(tmp_path, monkeypatch):
    from src.tools_rag import content_index as module

    i, _, _, _, _, _, _ = make_index(tmp_path)
    for kwargs in [
        dict(limit=True),
        dict(source_ids=[]),
        dict(source_ids=("\ud800",)),
        dict(content_types=("invalid",)),
    ]:
        with pytest.raises(RetrievalFault, match="invalid_parameter"):
            hits(i, **kwargs)
    assert module.SLOTS.acquire(blocking=False)
    assert module.SLOTS.acquire(blocking=False)
    try:
        with pytest.raises(Busy):
            hits(i)
    finally:
        module.SLOTS.release()
        module.SLOTS.release()
    monkeypatch.setattr(module, "QUERY_SECONDS", -1)
    with pytest.raises(Unavailable):
        hits(i)
    monkeypatch.setattr(module, "QUERY_SECONDS", 2)
    monkeypatch.setattr(module, "MAX_IO", 1)
    with pytest.raises(Unavailable):
        hits(i)
    monkeypatch.setattr(module, "MAX_IO", 128 * 1024**2)
    _, active, manifest = i._active()
    path = (
        i.root
        / "generations"
        / active.generation_id.split(":")[1]
        / active.build_id
        / manifest.files[0].name
    )
    original = path.read_bytes()
    target = tmp_path / "foreign-sqlite"
    target.write_bytes(original)
    target.chmod(0o600)
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(Unavailable):
        hits(i)
    path.unlink()
    path.write_bytes(original)
    path.chmod(0o600)
    assert hits(i).items
