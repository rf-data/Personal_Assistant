"""Actual ContentStore + shared lifecycle, fake encoding/transport only."""

import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.content_store.errors import (
    Busy,
    Forbidden,
    IntegrityError,
    InvalidInput,
    Unavailable,
)
from src.content_store.models import SourceGrant
from src.job_control.models import Principal
from src.model_discovery.cs50_index import EmbeddingConfig, TranscriptPayload
from src.tools_rag.content_index import RetrievalFault
from src.tools_rag.content_vector_models import (
    ContentVectorConfig,
    ContentVectorPayload,
    HybridContract,
    VectorPartition,
)
from src.tools_rag.content_vector_transport import FakeContentTransport
from src.tools_rag.content_vectors import ContentRetrieval, ContentVectorIndex
from src.tools_rag.cs50_embeddings import FakeEmbedder
from tests.content_store_support import OTHER, OWNER, VIEWER
from tests.test_content_fts import inventory, make_index, synthetic_index


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*a, **kw):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)


def case(tmp_path, kind=None, *, build=True):
    if kind:
        lexical, store, v, _, selection, _, key = make_index(tmp_path, kind)
    else:
        lexical, store, v, selection, key = synthetic_index(tmp_path, count=4)
    engine = FakeEmbedder(
        EmbeddingConfig.fake(max_tokens=8).model_copy(update={"batch_size": 2})
    )
    config = ContentVectorConfig(
        schema_version=1, name="content_offline", embedding=engine.config
    )
    transport = FakeContentTransport()
    vector = ContentVectorIndex.initialize(
        store,
        tmp_path / "vector",
        cursor_key_file=key,
        config=config,
        embedder=engine,
        transport=transport,
        _synthetic=kind is None,
    )
    if build:
        vector.build(selection, actor=OWNER)
    return lexical, vector, v, selection, key


def search(index, query="Python", **kwargs):
    with index.search_vector(query, actor=kwargs.pop("actor", OWNER), **kwargs) as page:
        return page


def partition(index):
    _, active, manifest = index._active()
    data = index.files.read(
        "generations/"
        + active.generation_id.split(":")[1]
        + "/"
        + active.build_id
        + "/"
        + manifest.files[0].name
    )
    return VectorPartition.model_validate_json(data)


@pytest.mark.parametrize(
    "kind,query",
    [("code", "hello"), ("html", "hello"), ("pdf", "print"), ("srt", "Hallo")],
)
def test_b_adapters_restart_provenance_and_unchanged_bytes(tmp_path, kind, query):
    lexical, i, v, sel, key = case(tmp_path, kind)
    before = inventory(i.store.root)
    page = search(i, query)
    assert page.items and page.ranking_schema == "cosine_l2_v1"
    assert all(
        h.method == "vector"
        and h.components[0].backend == "content_vectors_fake"
        and h.source_id == v.source_id
        for h in page.items
    )
    assert len({h.index_record_id for h in page.items}) == len(page.items)
    assert i.last_upload.status == "done"
    clone = ContentVectorIndex(
        i.store,
        i.root,
        cursor_key_file=key,
        config=i.config,
        embedder=FakeEmbedder(i.config.embedding),
        transport=FakeContentTransport(snapshot=i.transport.snapshot()),
    )
    assert search(clone, query) == page
    for h in page.items:
        b = next(
            b
            for b in i.store.list_content_blocks(v.parsed_version_id, actor=OWNER).items
            if b.block_id == h.block_id
        )
        assert h.excerpt.text == b.text[h.excerpt.start : h.excerpt.end]
        assert h.anchor.text_sha256 == b.text_sha256
        assert str(tmp_path) not in h.model_dump_json()
        if kind == "srt":
            assert h.locators[0].time_status == "known"
    assert inventory(i.store.root) == before
    with ContentRetrieval(lexical=lexical, vector=i).search(
        query, actor=OWNER, method="lexical"
    ) as p:
        assert p.ranking_schema == "source_rrf_v1"


def test_exact_children_unicode_whitespace_and_unknown_time(tmp_path):
    _, i, _, _, _ = case(tmp_path)
    part = partition(i)
    assert len(part.plan.units) > 4
    with i.store._maintenance(), i.store._connection() as db:
        _, records, _, _ = i._export(db, i._active()[2].basis.selection, OWNER)
    for r in records:
        units = [p for p in part.plan.units if p.index_record_id == r.index_record_id]
        assert "".join(p.child_text for p in units) == r.body.search_text
        assert all(
            p.child_start >= r.body.start and p.child_end <= r.body.end for p in units
        )
        assert len({p.point_id for p in units}) == len(units)
        for p in units:
            assert (
                p.child_text
                == r.body.search_text[
                    p.child_start - r.body.start : p.child_end - r.body.start
                ]
            )
            with pytest.raises(ValidationError):
                TranscriptPayload.model_validate(p.model_dump(mode="json"))
    assert all(
        h.locators[0].time_status == "unknown" and h.locators[0].start is None
        for h in search(i).items
    )


@pytest.mark.parametrize(
    "change",
    ["schema_version", "child_text_sha256", "child_start", "embedding_revision"],
)
def test_invalid_payload_not_adopted(tmp_path, change):
    _, i, _, _, _ = case(tmp_path)
    unit = partition(i).plan.units[0]
    d = unit.model_dump(mode="json")
    d[change] = (
        2
        if change == "schema_version"
        else 999
        if change == "child_start"
        else "0" * 64
        if change == "child_text_sha256"
        else "other"
    )
    if change != "embedding_revision":
        with pytest.raises(ValidationError):
            ContentVectorPayload.model_validate(d)
    else:
        assert ContentVectorPayload.model_validate(d).point_id != unit.point_id
    points = i.transport.collections[unit.collection_name]["points"]
    points[unit.point_id]["payload"] = d
    with pytest.raises(IntegrityError):
        search(i)


def test_partial_upsert_resume_readback_and_identical_generation(tmp_path, monkeypatch):
    _, i, _, sel, key = case(tmp_path, build=False)
    original = i.transport.upsert

    def interrupted(c, batch):
        original(c, dict(list(batch.items())[:1]))
        raise OSError("synthetic partial write")

    monkeypatch.setattr(i.transport, "upsert", interrupted)
    before = inventory(i.store.root)
    with pytest.raises(OSError):
        i.build(sel, actor=OWNER)
    assert i._active()[1] is None and not search(i).items
    assert i.last_upload.status == "failed"
    stopped = next(r for r in i.inspect_builds(actor=OWNER) if r.state == "failed")
    transport = FakeContentTransport(snapshot=i.transport.snapshot())
    resumed = ContentVectorIndex(
        i.store,
        i.root,
        cursor_key_file=key,
        config=i.config,
        embedder=FakeEmbedder(i.config.embedding),
        transport=transport,
        _synthetic=True,
    )
    wrong_engine = FakeEmbedder(EmbeddingConfig.fake(dimension=32, max_tokens=8))
    wrong = ContentVectorIndex(
        i.store,
        i.root,
        cursor_key_file=key,
        config=ContentVectorConfig(
            schema_version=1, name="content_offline", embedding=wrong_engine.config
        ),
        embedder=wrong_engine,
        transport=transport,
        _synthetic=True,
    )
    with pytest.raises(IntegrityError):
        wrong.resume(stopped.build_id, actor=OWNER)
    with pytest.raises(Forbidden):
        resumed.resume(stopped.build_id, actor=OTHER)
    active = resumed.resume(stopped.build_id, actor=OWNER)
    assert (
        active.generation_id == stopped.generation_id
        and resumed.last_upload.status == "done"
    )
    assert search(resumed).items and inventory(i.store.root) == before
    monkeypatch.setattr(
        transport,
        "upsert",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not reupload")),
    )
    same = resumed.build(sel, actor=OWNER)
    assert same.generation_id == active.generation_id
    resumed.discard_build(stopped.build_id, actor=OWNER)


def test_acknowledged_but_incomplete_readback_never_activates(tmp_path, monkeypatch):
    _, i, _, sel, _ = case(tmp_path, build=False)
    original = i.transport.upsert
    monkeypatch.setattr(
        i.transport, "upsert", lambda c, b: original(c, dict(list(b.items())[:-1]))
    )
    with pytest.raises(Unavailable):
        i.build(sel, actor=OWNER)
    assert i._active()[1] is None
    monkeypatch.setattr(i.transport, "upsert", original)
    assert i.build(sel, actor=OWNER).state == "active"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), 2.0, "0.5"])
def test_invalid_scores_are_rejected(tmp_path, monkeypatch, bad):
    _, i, _, _, _ = case(tmp_path)
    original = i.transport.query

    def corrupt(*a, **k):
        rows = original(*a, **k)
        rows[0]["score"] = bad
        return rows

    monkeypatch.setattr(i.transport, "query", corrupt)
    with pytest.raises(IntegrityError):
        search(i)


@pytest.mark.parametrize("field", ["dimension", "distance", "metadata", "indexes"])
def test_collection_contract_not_just_name(tmp_path, field):
    _, i, _, _, _ = case(tmp_path)
    c = i.transport.collections[partition(i).plan.collection.name]
    c[field] = (
        {"cs50_contract": {}}
        if field == "metadata"
        else []
        if field == "indexes"
        else 17
        if field == "dimension"
        else "Dot"
    )
    with pytest.raises(IntegrityError):
        search(i)


def test_live_grants_scope_no_backend_requests_or_hidden_counts(tmp_path, monkeypatch):
    _, i, v, _, _ = case(tmp_path)
    assert not search(i, actor=OTHER).items and not i.transport.requests
    assert not search(i, source_ids=("unknown",)).items
    assert not search(
        i, actor=Principal(subject=OWNER.subject, role="operator", courses=())
    ).items
    i.store.set_source_grants(
        v.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert search(i, actor=VIEWER).items
    i.store.set_source_grants(v.source_id, (), expected_acl_revision=1, actor=OWNER)
    calls = len(i.transport.requests)
    assert not search(i, actor=VIEWER).items and len(i.transport.requests) == calls
    with pytest.raises(Forbidden):
        search(i, actor="owner")
    assert "total_count" not in search(i).model_dump_json()


@pytest.mark.parametrize("target", ["source", "source_version", "parsed"])
def test_status_changes_fail_closed(tmp_path, target):
    _, i, v, _, _ = case(tmp_path)
    table, key, id_ = {
        "source": ("sources", "id", v.source_id),
        "source_version": ("source_versions", "id", v.source_version_id),
        "parsed": ("parsed_versions", "id", v.parsed_version_id),
    }[target]
    state = "tombstoned" if target == "source" else "quarantined"
    with i.store._maintenance(), i.store._connection(write=True) as db:
        db.execute(f"UPDATE {table} SET state=? WHERE {key}=?", (state, id_))
    if target == "source":
        assert not search(i).items
    else:
        with pytest.raises(RetrievalFault, match="stale_index"):
            search(i)


def test_pagination_ties_dedup_cursor_domain_and_generation(tmp_path):
    lexical, i, v, sel, key = case(tmp_path)
    a = search(i, limit=1)
    b = search(i, limit=1, cursor=a.next_cursor)
    assert a.items[0].index_record_id != b.items[0].index_record_id
    all_ids = []
    p = a
    while True:
        all_ids.extend(h.index_record_id for h in p.items)
        if not p.next_cursor:
            break
        p = search(i, limit=1, cursor=p.next_cursor)
    assert len(all_ids) == len(set(all_ids)) == 4
    full = search(i).items
    assert all_ids == [h.index_record_id for h in full]
    assert list(full) == sorted(
        full, key=lambda h: (-h.ranking_score, h.index_record_id)
    )
    part = partition(i)
    q = i.embedder.encode(["Python"], query=True)[0]
    for h in full:
        scores = [
            sum(a * b for a, b in zip(q, v, strict=True))
            for p, v in zip(part.plan.units, part.artifact.vectors, strict=True)
            if p.index_record_id == h.index_record_id
        ]
        assert h.ranking_score == max(scores)
    with pytest.raises(RetrievalFault, match="invalid_cursor"):
        search(i, "other", limit=1, cursor=a.next_cursor)
    with pytest.raises(RetrievalFault, match="invalid_cursor"):
        with lexical.search_lexical(
            "Python", actor=OWNER, limit=1, cursor=a.next_cursor
        ):
            pass
    with pytest.raises(Unavailable):
        ContentRetrieval(lexical=lexical, vector=i).search(
            "Python", method="hybrid", actor=OWNER
        )
    assert HybridContract(schema_version=1).activation == "blocked_pending_pilot"
    i.build(sel, actor=OWNER)
    assert search(i, limit=1, cursor=a.next_cursor) == b
    i.store.set_source_grants(v.source_id, (), expected_acl_revision=0, actor=OWNER)
    with pytest.raises(RetrievalFault, match="snapshot_changed"):
        search(i, limit=1, cursor=a.next_cursor)


def test_embedding_errors_and_real_pilot_gate(tmp_path, monkeypatch):
    _, i, _, sel, key = case(tmp_path)
    original = i.embedder.encode
    monkeypatch.setattr(
        i.embedder, "encode", lambda texts, **kw: [[0.0] * 16 for _ in texts]
    )
    with pytest.raises(ValueError):
        i.build(sel, actor=OWNER)
    monkeypatch.setattr(i.embedder, "encode", original)
    assert search(i).items
    with pytest.raises(Forbidden):
        ContentVectorIndex.initialize(
            i.store,
            tmp_path / "blocked",
            cursor_key_file=key,
            config=i.config,
            embedder=object(),
            transport=i.transport,
            _synthetic=True,
        )
    assert not (tmp_path / "blocked").exists()
    with pytest.raises(ValidationError):
        EmbeddingConfig(revision="latest")
    transport = i.transport
    i.transport = object()
    with pytest.raises(Forbidden):
        search(i)
    i.transport = transport
    with pytest.raises(InvalidInput):
        ContentVectorIndex(
            i.store,
            i.root,
            cursor_key_file=key,
            config=i.config,
            embedder=FakeEmbedder(EmbeddingConfig.fake(dimension=32)),
            transport=i.transport,
            _synthetic=True,
        )


def test_writer_guard_and_acl_change_during_build(tmp_path, monkeypatch):
    _, i, v, sel, _ = case(tmp_path)
    with i.search_vector("Python", actor=OWNER) as page:
        assert page.items
        with pytest.raises(Busy):
            i.store.set_source_grants(
                v.source_id, (), expected_acl_revision=0, actor=OWNER
            )
        with pytest.raises(Busy):
            i.build(sel, actor=OWNER)
    original = i.transport.read
    changed = []

    def change(c):
        if not changed:
            i.store.set_source_grants(
                v.source_id, (), expected_acl_revision=0, actor=OWNER
            )
            changed.append(True)
        return original(c)

    monkeypatch.setattr(i.transport, "read", change)
    before = i._active()[1]
    with pytest.raises(Unavailable):
        i.build(sel, actor=OWNER)
    assert i._active()[1] == before


def test_process_reopen_from_explicit_fake_snapshot(tmp_path):
    _, i, _, _, key = case(tmp_path)
    p = tmp_path / "fake-transport.json"
    p.write_text(json.dumps(i.transport.snapshot()))
    script = """
import json,sys
from src.content_store.store import ContentStore
from src.tools_rag.content_vectors import ContentVectorIndex
from src.tools_rag.content_vector_models import ContentVectorConfig
from src.tools_rag.content_vector_transport import FakeContentTransport
from src.tools_rag.cs50_embeddings import FakeEmbedder
from tests.content_store_support import OWNER
c=ContentVectorConfig.model_validate_json(sys.argv[4])
i=ContentVectorIndex(ContentStore(sys.argv[1]),sys.argv[2],cursor_key_file=sys.argv[3],config=c,embedder=FakeEmbedder(c.embedding),transport=FakeContentTransport(snapshot=json.load(open(sys.argv[5]))),_synthetic=True)
with i.search_vector('Python',actor=OWNER) as p:print(p.model_dump_json())
"""
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(i.store.root),
            str(i.root),
            str(key),
            i.config.model_dump_json(),
            str(p),
        ],
        env={
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": "/usr/lib/python3/dist-packages",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == search(i).model_dump(mode="json")


def test_combining_text_record_offsets_and_model_change(tmp_path):
    from src.content_store._testing import publish_synthetic
    from src.content_store.index_models import IndexProjectionConfig
    from src.tools_rag.content_index_models import IndexSelection
    from tests.content_store_support import config, payload

    _, i, v, sel, key = case(tmp_path)
    raw = partition(i).plan.units[0]
    original = "A\u0308 😀\n    print('é')\r\n" * 3
    sv = next(
        s
        for s in i.store.list_source_versions(v.source_id, actor=OWNER)
        if s.source_version_id == v.source_version_id
    )
    v2 = publish_synthetic(
        i.store,
        v.source_version_id,
        payload(sv.manifest.artifacts[0].sha256, text=original),
        config(implementation_revision="unicode-other"),
        actor=OWNER,
        request_key="unicode-other",
    ).version
    sel = IndexSelection(
        parsed_version_ids=(v2.parsed_version_id,),
        config=IndexProjectionConfig(schema_version=1, max_codepoints=12),
    )
    i.build(sel, actor=OWNER)
    part = partition(i)
    units = [p for p in part.plan.units if p.block_id == "synthetic-block:1"]
    assert "".join(p.child_text for p in units) == original
    assert any(p.record_start > 0 and p.child_start >= p.record_start for p in units)
    assert {p.point_id for p in part.plan.units}.isdisjoint({raw.point_id})
    engine = FakeEmbedder(EmbeddingConfig.fake(dimension=32, max_tokens=8))
    other_config = ContentVectorConfig(
        schema_version=1, name="content_other", embedding=engine.config
    )
    incompatible = ContentVectorIndex(
        i.store,
        i.root,
        cursor_key_file=key,
        config=other_config,
        embedder=engine,
        transport=i.transport,
        _synthetic=True,
    )
    with pytest.raises(Unavailable):
        search(incompatible)
    with pytest.raises(Unavailable):
        incompatible.build(sel, actor=OWNER)
    other = ContentVectorIndex.initialize(
        i.store,
        tmp_path / "new-model-index",
        cursor_key_file=key,
        config=other_config,
        embedder=engine,
        transport=i.transport,
        _synthetic=True,
    )
    other.build(sel, actor=OWNER)
    new = partition(other)
    assert {p.index_record_id for p in new.plan.units} == {
        p.index_record_id for p in part.plan.units
    }
    assert {p.point_id for p in new.plan.units}.isdisjoint(
        p.point_id for p in part.plan.units
    )
    from src.content_store._testing import register_synthetic_version
    from src.content_store.models import RawArtifact, RawManifest
    from tests.content_store_support import raw as store_raw

    ref = store_raw(i.store, v.source_id, b"new vector synthetic raw version")
    changed_sv = register_synthetic_version(
        i.store,
        v.source_id,
        RawManifest(artifacts=(RawArtifact(**ref.model_dump()),)),
        actor=OWNER,
    )
    changed = publish_synthetic(
        i.store,
        changed_sv.source_version_id,
        payload(ref.sha256, text=original),
        config(),
        actor=OWNER,
        request_key="changed-raw-vector",
    ).version
    other.build(
        IndexSelection(parsed_version_ids=(changed.parsed_version_id,)), actor=OWNER
    )
    assert {p.source_version_id for p in partition(other).plan.units} == {
        changed_sv.source_version_id
    }


def test_foreign_collections_are_never_queried_and_scope_does_not_leak(tmp_path):
    from src.content_store._testing import publish_synthetic, register_synthetic_version
    from src.content_store.models import RawArtifact, RawManifest
    from src.tools_rag.content_index_models import IndexSelection
    from tests.content_store_support import config, payload, raw, registration

    _, i, v, _, _ = case(tmp_path)
    i.store.set_source_grants(
        v.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    before = search(i, actor=VIEWER)
    source = i.store.register_source(registration("foreign-vector"), actor=OWNER)
    ref = raw(i.store, source.source_id)
    sv = register_synthetic_version(
        i.store,
        source.source_id,
        RawManifest(artifacts=(RawArtifact(**ref.model_dump()),)),
        actor=OWNER,
    )
    v2 = publish_synthetic(
        i.store,
        sv.source_version_id,
        payload(ref.sha256, text="Python foreign"),
        config(),
        actor=OWNER,
        request_key="foreign-vector",
    ).version
    i.build(
        IndexSelection(
            parsed_version_ids=tuple(
                sorted([v.parsed_version_id, v2.parsed_version_id])
            )
        ),
        actor=OWNER,
    )
    for c in i.transport.collections.values():
        if c["metadata"]["content_vector_contract"]["source_id"] == source.source_id:
            c["points"] = {"foreign-corruption": {}}
    i.transport.requests.clear()
    after = search(i, actor=VIEWER)
    assert [h.model_dump(exclude={"index_generation"}) for h in before.items] == [
        h.model_dump(exclude={"index_generation"}) for h in after.items
    ]
    assert all(
        source.source_id not in req["scope"]["source_id"]
        for req in i.transport.requests
    )
    assert source.source_id not in after.model_dump_json()
    with pytest.raises((Unavailable, IntegrityError)):
        search(i)


def test_missing_partition_or_collection_has_no_lexical_fallback(tmp_path):
    lexical, i, _, _, _ = case(tmp_path)
    part = partition(i)
    _, active, manifest = i._active()
    path = (
        i.root
        / "generations"
        / active.generation_id.split(":")[1]
        / active.build_id
        / manifest.files[0].name
    )
    data = path.read_bytes()
    path.unlink()
    with pytest.raises(Unavailable):
        search(i)
    path.write_bytes(data)
    path.chmod(0o600)
    i.transport.collections.pop(part.plan.collection.name)
    with pytest.raises(Unavailable):
        search(i)
    with lexical.search_lexical("Python", actor=OWNER) as page:
        assert page.items


def test_empty_selection_and_fail_before_embedding(tmp_path, monkeypatch):
    from src.tools_rag.content_index_models import IndexSelection

    _, i, _, sel, _ = case(tmp_path, build=False)
    original = i.embedder.encode
    monkeypatch.setattr(
        i.embedder,
        "encode",
        lambda *a, **k: (_ for _ in ()).throw(OSError("encoding interrupted")),
    )
    with pytest.raises(OSError):
        i.build(sel, actor=OWNER)
    assert not i.transport.collections and not search(i).items
    monkeypatch.setattr(i.embedder, "encode", original)
    assert i.build(IndexSelection(parsed_version_ids=()), actor=OWNER).state == "active"
    assert not search(i).items


def test_shared_legacy_collection_gate_without_sdk():
    from types import SimpleNamespace as NS

    from src.model_discovery.cs50_index import CollectionContract
    from src.tools_rag.cs50_collection import check_configuration

    contract = CollectionContract(embedding=EmbeddingConfig.fake())
    info = NS(
        config=NS(
            params=NS(vectors=NS(size=16, distance=NS(value="Cosine"))),
            metadata={"cs50_contract": contract.model_dump(mode="json")},
        )
    )
    assert check_configuration(info, contract) is info
    info.config.params.vectors.size = 32
    with pytest.raises(ValueError):
        check_configuration(info, contract)
    info.config.params.vectors.size = 16
    info.config.metadata = {"content_vector_contract": contract.model_dump(mode="json")}
    with pytest.raises(ValueError):
        check_configuration(info, contract)
