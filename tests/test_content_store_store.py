import io
import json
import sqlite3
import subprocess
import sys

import pytest
from content_store_support import (
    OTHER,
    OWNER,
    RAW,
    VIEWER,
    config,
    payload,
    raw,
    registration,
    seeded,
)

from src.content_store import ContentStore
from src.content_store._testing import (
    publish_synthetic,
    register_synthetic_version,
)
from src.content_store.errors import (
    Busy,
    Conflict,
    Forbidden,
    IntegrityError,
    InvalidInput,
    NotFound,
    Unavailable,
    UnverifiedBinding,
)
from src.content_store.models import RawArtifact, RawManifest, SourceGrant, sha256
from src.content_store.schema import TABLES


def inventory(root):
    return {
        str(p.relative_to(root)): (
            p.stat().st_mode,
            p.read_bytes() if p.is_file() else None,
        )
        for p in root.rglob("*")
    }


def publish(store, ref, version, **kwargs):
    return publish_synthetic(
        store,
        version.source_version_id,
        payload(ref.sha256),
        config(),
        actor=OWNER,
        **kwargs,
    )


def test_t01_initialize_wal_fk_full_and_no_implicit_database(tmp_path):
    absent = tmp_path / "absent"
    with pytest.raises(Unavailable):
        ContentStore(absent)
    assert not absent.exists()
    empty = tmp_path / "empty"
    empty.mkdir(mode=0o700)
    with pytest.raises(Unavailable):
        ContentStore(empty)
    assert list(empty.iterdir()) == []
    store = ContentStore.initialize(empty)
    with store._connection() as db:
        assert db.execute("SELECT identity FROM metadata").fetchone()[0] == "content-v1"
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert {
            r[0]
            for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        } == set(TABLES)
    with store._connection(write=True) as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    before = inventory(empty)
    reader = ContentStore(empty)
    assert reader.list_sources(actor=OWNER) == ()
    assert inventory(empty) == before
    with pytest.raises(Forbidden):
        reader.register_source(registration(), actor=OWNER)


def test_t01_existing_root_and_foreign_database_not_adopted(tmp_path):
    root = tmp_path / "foreign"
    root.mkdir(mode=0o700)
    foreign = root / "jobs.sqlite3"
    foreign.write_bytes(b"foreign original sentinel")
    with pytest.raises(Unavailable):
        ContentStore.initialize(root)
    assert foreign.read_bytes() == b"foreign original sentinel"
    assert set(root.iterdir()) == {foreign}


@pytest.mark.parametrize(
    "mutation",
    [
        "PRAGMA user_version=2",
        "PRAGMA application_id=0",
        "DROP TABLE content_locators",
        "DROP INDEX active_slot",
    ],
)
def test_t01_unknown_or_damaged_schema_rejected(tmp_path, mutation):
    store = ContentStore.initialize(tmp_path / "content")
    with store._connection(write=True) as db:
        db.execute(mutation)
    before = inventory(store.root)
    with pytest.raises(Unavailable):
        ContentStore(store.root)
    assert inventory(store.root) == before


def test_t01_database_bytes_corrupt_controlled(tmp_path):
    store = ContentStore.initialize(tmp_path / "content")
    (store.root / "content.sqlite3").write_bytes(b"not sqlite")
    with pytest.raises(Unavailable):
        ContentStore(store.root)


def test_t02_raw_roundtrip_after_new_process_and_reimport(tmp_path):
    store = ContentStore.initialize(tmp_path / "content")
    source = store.register_source(registration(), actor=OWNER)
    ref = raw(store, source.source_id)
    assert raw(store, source.source_id) == ref
    assert (
        ContentStore(store.root).read_raw_artifact(
            source.source_id, ref.sha256, actor=OWNER
        )
        == RAW
    )
    program = "from src.content_store import ContentStore\nfrom src.job_control.models import Principal\nimport sys\ns=ContentStore(sys.argv[1]);a=Principal(subject='owner',role='operator',courses=('cs50_python',))\nsys.stdout.buffer.write(s.read_raw_artifact(sys.argv[2],sys.argv[3],actor=a))"
    result = subprocess.run(
        [sys.executable, "-c", program, str(store.root), source.source_id, ref.sha256],
        check=True,
        capture_output=True,
    )
    assert result.stdout == RAW


@pytest.mark.parametrize("wrong", ["hash", "size", "stream"])
def test_t02_invalid_bytes_block_run_without_raw_reference(tmp_path, wrong):
    store = ContentStore.initialize(tmp_path / "content")
    source = store.register_source(registration(), actor=OWNER)
    size = len(RAW) + (1 if wrong == "size" else 0)
    digest = "a" * 64 if wrong == "hash" else sha256(RAW)
    stream = io.StringIO("text") if wrong == "stream" else io.BytesIO(RAW)
    with pytest.raises((IntegrityError, InvalidInput)):
        store.store_raw_artifact(
            source.source_id,
            stream,
            expected_sha256=digest,
            expected_size=size,
            mime_type="text/plain",
            actor=OWNER,
        )
    with store._connection() as db:
        assert db.execute("SELECT count(*) FROM raw_reservations").fetchone()[0] == 0
        assert (
            db.execute("SELECT state FROM processing_runs").fetchone()[0] == "blocked"
        )
    with pytest.raises(NotFound):
        store.read_raw_artifact(source.source_id, digest, actor=OWNER)


def test_t02_corrupt_existing_blob_is_never_replaced(tmp_path):
    store = ContentStore.initialize(tmp_path / "content")
    first = store.register_source(registration("first"), actor=OWNER)
    second = store.register_source(registration("second"), actor=OTHER)
    ref = raw(store, first.source_id)
    target = store.root / ref.store_key
    target.write_bytes(b"x" * len(RAW))
    with pytest.raises(IntegrityError):
        raw(store, second.source_id, actor=OTHER)
    assert target.read_bytes() == b"x" * len(RAW)


def test_t03_source_identity_and_synthetic_verified_manifest(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    assert store.register_source(registration(), actor=OWNER) == source
    assert (
        register_synthetic_version(
            store, source.source_id, version.manifest, actor=OWNER
        )
        == version
    )
    assert store.list_source_versions(source.source_id, actor=OWNER) == (version,)
    with pytest.raises(Conflict):
        store.register_source(
            registration().model_copy(update={"source_origin": "official"}), actor=OWNER
        )
    foreign = store.register_source(registration("foreign"), actor=OWNER)
    with pytest.raises(IntegrityError):
        register_synthetic_version(
            store, foreign.source_id, version.manifest, actor=OWNER
        )


def test_public_verification_and_publish_are_closed_even_in_test_store(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    with pytest.raises(UnverifiedBinding):
        store.register_source_version(
            source.source_id,
            version.manifest,
            variant_key="default",
            binding={"verified": True},
            actor=OWNER,
        )
    with pytest.raises(Unavailable):
        store.publish_parsed_document(
            version.source_version_id,
            {"arbitrary": "payload"},
            actor=OWNER,
            request_key="any",
        )
    ordinary = ContentStore.initialize(tmp_path / "ordinary")
    ordinary_source = ordinary.register_source(registration(), actor=OWNER)
    ordinary_ref = raw(ordinary, ordinary_source.source_id)
    manifest = RawManifest(artifacts=(RawArtifact(**ordinary_ref.model_dump()),))
    with pytest.raises(Forbidden):
        register_synthetic_version(
            ordinary, ordinary_source.source_id, manifest, actor=OWNER
        )
    assert ordinary._purpose == "content"


def test_t04_parsed_exact_roundtrip_and_redacted_views(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    result = publish(store, ref, version)
    reader = ContentStore(store.root)
    before = inventory(store.root)
    view = reader.get_parsed_document(result.version.parsed_version_id, actor=OWNER)
    expected = payload(ref.sha256)
    assert view.payload_sha256 == sha256(expected)
    assert reader.read_parsed_payload(view.parsed_version_id, actor=OWNER) == expected
    page = reader.list_content_blocks(view.parsed_version_id, actor=OWNER)
    assert [b.type for b in page.items] == [
        "heading",
        "paragraph",
        "code",
        "formula",
        "image_reference",
    ]
    assert [b.order for b in page.items] == list(range(5))
    original = json.loads(expected)["blocks"]
    assert [b.model_dump(mode="json") for b in page.items] == original
    assert page.items[1].locators[0].start == 1.25
    assert page.items[0].locators[0].start is None
    assert page.items[4].data["availability"] == "reference_only"
    assert str(store.root) not in view.model_dump_json()
    assert (
        "owner_subject"
        not in reader.get_source(source.source_id, actor=OWNER).model_dump_json()
    )
    assert inventory(store.root) == before


def test_t05_idempotence_keys_slots_and_changed_parser(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    first = publish(store, ref, version, request_key="first")
    again = publish(store, ref, version, request_key="first")
    different_key = publish(store, ref, version, request_key="second")
    assert first.created and not again.created and not different_key.created
    assert first.version == again.version == different_key.version
    changed = payload(ref.sha256, text="changed + minus -")
    with pytest.raises(Conflict):
        publish_synthetic(
            store,
            version.source_version_id,
            changed,
            config(),
            actor=OWNER,
            request_key="third",
        )
    assert publish(store, ref, version, request_key="fourth").version == first.version
    with pytest.raises(Conflict):
        publish_synthetic(
            store,
            version.source_version_id,
            changed,
            config(parser_version="2"),
            actor=OWNER,
            request_key="first",
        )
    next_parser = publish_synthetic(
        store,
        version.source_version_id,
        changed,
        config(parser_version="2"),
        actor=OWNER,
        request_key="parser2",
    )
    assert next_parser.version.source_version_id == first.version.source_version_id
    assert next_parser.version.parsed_version_id != first.version.parsed_version_id
    with store._connection() as db:
        assert db.execute("SELECT count(*) FROM parsed_versions").fetchone()[0] == 2


def test_t06_owner_course_grants_and_no_hash_authorization(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    result = publish(store, ref, version)
    for actor in (VIEWER, OTHER, OWNER.model_copy(update={"courses": ("cs50x",)})):
        with pytest.raises(Forbidden):
            store.get_source(source.source_id, actor=actor)
        with pytest.raises(Forbidden):
            store.get_parsed_document(result.version.parsed_version_id, actor=actor)
        assert store.list_sources(actor=actor) == ()
    store.set_source_grants(
        source.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert (
        store.get_source(source.source_id, actor=VIEWER).source_id == source.source_id
    )
    assert store.read_raw_artifact(source.source_id, ref.sha256, actor=VIEWER) == RAW
    with pytest.raises(Forbidden):
        raw(store, source.source_id, actor=VIEWER)
    with pytest.raises(Conflict):
        store.set_source_grants(
            source.source_id, (), expected_acl_revision=0, actor=OWNER
        )
    other_source = store.register_source(registration("other"), actor=OTHER)
    assert raw(store, other_source.source_id, actor=OTHER) == ref
    with pytest.raises(Forbidden):
        store.read_raw_artifact(source.source_id, ref.sha256, actor=OTHER)
    assert [s.source_id for s in store.list_sources(actor=OTHER)] == [
        other_source.source_id
    ]


def test_t06_acl_is_rechecked_after_staging(tmp_path, monkeypatch):
    store, source, ref, version = seeded(tmp_path)
    install = store._artifacts.install

    def revoke_during_install(run_id, reference):
        install(run_id, reference)
        if reference.sha256 == sha256(payload(ref.sha256)):
            store.set_source_grants(
                source.source_id,
                (SourceGrant(subject=VIEWER.subject),),
                expected_acl_revision=0,
                actor=OWNER,
            )

    monkeypatch.setattr(store._artifacts, "install", revoke_during_install)
    with pytest.raises(Forbidden):
        publish(store, ref, version)
    with store._connection() as db:
        assert db.execute("SELECT count(*) FROM parsed_versions").fetchone()[0] == 0


def test_t07_failure_before_final_commit_preserves_prepared_evidence(
    tmp_path, monkeypatch
):
    store, source, ref, version = seeded(tmp_path)
    update = store._update_run

    def fail_commit(db, run, **updates):
        if updates.get("state") == "committed":
            raise sqlite3.OperationalError("synthetic injected disk error")
        return update(db, run, **updates)

    with monkeypatch.context() as m:
        m.setattr(store, "_update_run", fail_commit)
        with pytest.raises(Unavailable):
            publish(store, ref, version)
    with store._connection() as db:
        assert db.execute("SELECT count(*) FROM parsed_versions").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM content_blocks").fetchone()[0] == 0
        row = db.execute(
            "SELECT data FROM processing_runs WHERE kind='synthetic'"
        ).fetchone()
        run = json.loads(row[0])
        assert run["state"] == "blocked" and len(run["manifest"]) == 2
    assert store.list_source_versions(source.source_id, actor=OWNER) == (version,)
    with pytest.raises(Unavailable):
        publish(store, ref, version)
    with pytest.raises(Busy):
        publish(store, ref, version, request_key="new-key")


def test_t07_constraints_rollback_and_immutable_versions(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    result = publish(store, ref, version)
    with store._connection() as db:
        revision = db.execute("SELECT collection_revision FROM metadata").fetchone()[0]
    with pytest.raises(IntegrityError):
        with store._connection(write=True) as db:
            db.execute("UPDATE metadata SET collection_revision=999 WHERE id=1")
            db.execute(
                "INSERT INTO source_grants VALUES ('nonexistent','viewer','read')"
            )
    with store._connection() as db:
        assert (
            db.execute("SELECT collection_revision FROM metadata").fetchone()[0]
            == revision
        )
    for sql in (
        "UPDATE parsed_versions SET payload_sha256='other'",
        "DELETE FROM content_blocks",
        "UPDATE parser_configs SET data='{}'",
    ):
        with pytest.raises(IntegrityError):
            with store._connection(write=True) as db:
                db.execute(sql)
    assert store.get_parsed_document(result.version.parsed_version_id, actor=OWNER)


def test_t07_corrupt_payload_stops_reads_without_repair(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    result = publish(store, ref, version)
    target = store.root / result.version.payload.store_key
    target.write_bytes(b"corrupt")
    with pytest.raises(IntegrityError):
        store.get_parsed_document(result.version.parsed_version_id, actor=OWNER)
    assert target.read_bytes() == b"corrupt"


def test_t07_busy_lock_and_wal_are_fail_closed(tmp_path):
    store = ContentStore.initialize(tmp_path / "content")
    with store._artifacts.lock(".content-db.lock", exclusive=True):
        with pytest.raises(Busy):
            store.get_source("unknown", actor=OWNER)
    wal = store.root / "content.sqlite3-wal"
    wal.write_bytes(b"incomplete WAL requires recovery")
    wal.chmod(0o600)
    before = inventory(store.root)
    with pytest.raises(Unavailable):
        ContentStore(store.root)
    assert inventory(store.root) == before


def test_pagination_does_not_return_a_silently_truncated_page(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    result = publish(store, ref, version)
    with pytest.raises(Unavailable):
        store.list_content_blocks(
            result.version.parsed_version_id, actor=OWNER, limit=2
        )
    with pytest.raises(Unavailable):
        store.list_sources(actor=OWNER, cursor="untrusted")
    with pytest.raises(InvalidInput):
        store.list_sources(actor=OWNER, limit=True)


def test_t03_actual_registration_preserves_cs50_ids(tmp_path):
    from src.content_store.models import SourceRegistration
    from src.model_discovery.cs50 import ResourceCandidate

    candidate = ResourceCandidate(
        course_id="cs50_python",
        role="notes",
        original_url="https://cs50.harvard.edu/python/notes/0/",
    )
    store = ContentStore.initialize(tmp_path / "content")
    source = store.register_source(
        SourceRegistration(
            identity_namespace="cs50",
            external_identity=candidate.resource_id,
            source_id=candidate.resource_id,
            course_id=candidate.course_id,
            source_type="material",
            source_origin="official",
        ),
        actor=OWNER,
    )
    assert source.source_id == candidate.resource_id
    assert (
        ContentStore(store.root).get_source(source.source_id, actor=OWNER).source_id
        == candidate.resource_id
    )
    assert str(candidate.original_url) == "https://cs50.harvard.edu/python/notes/0/"


def test_t05_new_raw_version_preserves_the_previous_version(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    previous = publish(store, ref, version)
    new_ref = raw(store, source.source_id, b"new original bytes")
    new_version = register_synthetic_version(
        store,
        source.source_id,
        RawManifest(artifacts=(RawArtifact(**new_ref.model_dump()),)),
        actor=OWNER,
    )
    assert new_version.source_version_id != version.source_version_id
    assert store.read_raw_artifact(source.source_id, ref.sha256, actor=OWNER) == RAW
    assert store.get_parsed_document(previous.version.parsed_version_id, actor=OWNER)


def test_t02_raw_reimport_supports_short_reads_and_rejects_false_content(tmp_path):
    store, source, ref, version = seeded(tmp_path)

    class ShortReads(io.BytesIO):
        def read(self, size=-1):
            return super().read(min(size, 3))

    assert (
        store.store_raw_artifact(
            source.source_id,
            ShortReads(RAW),
            expected_sha256=ref.sha256,
            expected_size=len(RAW),
            mime_type=ref.mime_type,
            actor=OWNER,
        )
        == ref
    )
    with pytest.raises(IntegrityError):
        store.store_raw_artifact(
            source.source_id,
            io.BytesIO(b"x" * len(RAW)),
            expected_sha256=ref.sha256,
            expected_size=len(RAW),
            mime_type=ref.mime_type,
            actor=OWNER,
        )


@pytest.mark.parametrize(
    "mutation",
    ["missing_marker", "duplicate_key", "invalid_json", "non_finite", "wrong_origin"],
)
def test_synthetic_contract_rejects_ambiguous_or_unmarked_payload(tmp_path, mutation):
    store, source, ref, version = seeded(tmp_path)
    data = payload(ref.sha256)
    if mutation == "missing_marker":
        obj = json.loads(data)
        obj.pop("source_origin")
        data = json.dumps(obj).encode()
    elif mutation == "duplicate_key":
        data = data.replace(
            b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1'
        )
    elif mutation == "invalid_json":
        data = b"{"
    elif mutation == "non_finite":
        data = data.replace(b'"data": {}', b'"data": {"number": NaN}', 1)
    else:
        data = data.replace(ref.sha256.encode(), b"a" * 64)
    with pytest.raises((InvalidInput, IntegrityError)):
        publish_synthetic(store, version.source_version_id, data, config(), actor=OWNER)
    with store._connection() as db:
        assert db.execute("SELECT count(*) FROM parsed_versions").fetchone()[0] == 0


def test_t07_actual_process_exit_never_publishes_partial_content(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    program = """
import os,sys
sys.path.insert(0,'tests')
from content_store_support import OWNER,config,payload
from src.content_store import ContentStore
from src.content_store._testing import publish_synthetic
s=ContentStore(sys.argv[1],read_only=False)
original=s._update_run
def die(db,run,**updates):
    if updates.get('state')=='committed': os._exit(23)
    return original(db,run,**updates)
s._update_run=die
publish_synthetic(s,sys.argv[2],payload(sys.argv[3]),config(),actor=OWNER)
"""
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            program,
            str(store.root),
            version.source_version_id,
            ref.sha256,
        ],
        capture_output=True,
        timeout=20,
    )
    assert child.returncode == 23, child.stderr.decode()
    # Inspect the last checkpointed snapshot without SQLite performing WAL recovery.
    with sqlite3.connect(
        (store.root / "content.sqlite3").as_uri() + "?mode=ro&immutable=1", uri=True
    ) as db:
        assert db.execute("SELECT count(*) FROM parsed_versions").fetchone()[0] == 0
        assert (
            db.execute(
                "SELECT state FROM processing_runs WHERE kind='synthetic'"
            ).fetchone()[0]
            == "prepared"
        )
    before = inventory(store.root)
    try:
        reopened = ContentStore(store.root)
        with pytest.raises(NotFound):
            reopened.get_parsed_document("unpublished-version", actor=OWNER)
    except Unavailable:
        pass  # Nonempty WAL is deliberately blocked until explicit C23-02C recovery.
    assert inventory(store.root) == before


def test_t07_quarantine_status_blocks_even_byte_intact_artifacts(tmp_path):
    store, source, ref, version = seeded(tmp_path)
    result = publish(store, ref, version)
    with store._connection(write=True) as db:
        db.execute(
            "UPDATE artifacts SET state='quarantined' WHERE sha256=?",
            (result.version.payload.sha256,),
        )
    with pytest.raises(IntegrityError):
        store.get_parsed_document(result.version.parsed_version_id, actor=OWNER)


def test_synthetic_contract_cannot_promote_an_ordinary_store(tmp_path):
    store = ContentStore.initialize(tmp_path / "content")
    source = store.register_source(registration(), actor=OWNER)
    ref = raw(store, source.source_id)
    store._purpose = "synthetic_test"
    with pytest.raises(Forbidden):
        register_synthetic_version(
            store,
            source.source_id,
            RawManifest(artifacts=(RawArtifact(**ref.model_dump()),)),
            actor=OWNER,
        )
    with pytest.raises(IntegrityError):
        with store._connection(write=True) as db:
            db.execute("UPDATE metadata SET purpose='synthetic_test'")
    with store._connection() as db:
        assert db.execute("SELECT count(*) FROM source_versions").fetchone()[0] == 0
