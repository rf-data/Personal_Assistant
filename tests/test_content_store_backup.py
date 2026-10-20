import pytest

from src.content_store.adapters import import_verified_bundle, verify_srt_bundle
from src.content_store.backup import backup, restore
from src.content_store.errors import (
    ContentStoreError,
    Forbidden,
    Unavailable,
)
from src.content_store.models import SourceGrant
from src.content_store.store import ContentStore
from tests.content_adapter_support import srt
from tests.content_operations_support import child, launch, line, seeded, stop
from tests.content_store_support import OTHER, OWNER, VIEWER


def test_material_and_srt_backup_restore_separate_process(tmp_path):
    store, bundle, doc, first = seeded(tmp_path)
    sbundle, _ = srt(tmp_path / "srt")
    second = import_verified_bundle(
        store, verify_srt_bundle(sbundle), actor=OWNER, request_key="srt"
    )
    store.set_source_grants(
        doc.binding.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    # Unrelated adjacent/private data must never enter the snapshot.
    (store.root / "unrelated.token").write_bytes(b"synthetic unrelated secret")
    snapshot = tmp_path / "snapshot"
    before = (store.root / "content.sqlite3").read_bytes()
    manifest = backup(store, snapshot, actor=OWNER)
    assert (store.root / "content.sqlite3").read_bytes() == before
    assert not (snapshot / "unrelated.token").exists()
    restored = tmp_path / "restored"
    process = child("restore", restored, snapshot)
    assert line(process)["snapshot_id"] == manifest.snapshot.snapshot_id
    process.communicate(timeout=10)
    assert process.returncode == 0
    read = ContentStore(restored)
    assert (
        read.read_parsed_payload(first.version.parsed_version_id, actor=VIEWER)
        == bundle.normalized_path.read_bytes()
    )
    with pytest.raises(Forbidden):
        read.read_parsed_payload(second.version.parsed_version_id, actor=VIEWER)
    assert (
        read.read_parsed_payload(second.version.parsed_version_id, actor=OWNER)
        == sbundle.transcript_path.read_bytes()
    )
    assert (
        read.read_raw_artifact(doc.binding.source_id, doc.raw_sha256, actor=OWNER)
        == bundle.raw_path.read_bytes()
    )
    assert (
        read.read_version_artifact(
            first.version.parsed_version_id, "receipt", actor=OWNER
        )
        == bundle.receipt_path.read_bytes()
    )
    with pytest.raises(ContentStoreError):
        backup(store, snapshot, actor=OWNER)
    with pytest.raises(ContentStoreError):
        restore(snapshot, restored, actor=OWNER)


@pytest.mark.parametrize("damage", ["manifest", "db", "blob", "extra", "symlink"])
def test_corrupt_snapshot_rejected_before_destination(tmp_path, damage):
    store, _, _, result = seeded(tmp_path)
    snapshot = tmp_path / "snapshot"
    backup(store, snapshot, actor=OWNER)
    if damage == "manifest":
        (snapshot / "manifest.json").write_bytes(b"{}")
    elif damage == "db":
        (snapshot / "content.sqlite3").write_bytes(b"not sqlite")
    elif damage == "blob":
        (snapshot / result.version.payload.store_key).write_bytes(b"forged")
    elif damage == "extra":
        (snapshot / "extra.secret").write_bytes(b"no")
    else:
        (snapshot / "link").symlink_to(snapshot / "content.sqlite3")
    target = tmp_path / "restore"
    with pytest.raises(ContentStoreError):
        restore(snapshot, target, actor=OWNER)
    assert not target.exists()


def test_incomplete_backup_and_scope_are_not_success(tmp_path, monkeypatch):
    store, _, _, _ = seeded(tmp_path)
    for actor in (OTHER, VIEWER):
        with pytest.raises(Forbidden):
            backup(store, tmp_path / "denied", actor=actor)
    import src.content_store.backup as module

    def full(*a, **kw):
        raise OSError(28, "controlled disk full")

    monkeypatch.setattr(module, "_new_file", full)
    with pytest.raises(Unavailable):
        backup(store, tmp_path / "incomplete", actor=OWNER)
    assert not (tmp_path / "incomplete/manifest.json").exists()
    with pytest.raises(ContentStoreError):
        restore(tmp_path / "incomplete", tmp_path / "restore", actor=OWNER)


def test_quarantine_tombstone_and_incomplete_run_preserved(tmp_path):
    store, bundle, _, result = seeded(tmp_path)
    payload = result.version.payload
    path = store.root / payload.store_key
    data = path.read_bytes()
    path.write_bytes(b"corrupt")
    store.verify_integrity(actor=OWNER)
    path.write_bytes(data)
    # Quarantine is retained after byte restoration; backup is a capture, no release.
    with store._connection(write=True) as db:
        db.execute(
            "UPDATE sources SET state='tombstoned' WHERE id=?",
            (result.version.source_id,),
        )
    snapshot = tmp_path / "snapshot"
    backup(store, snapshot, actor=OWNER)
    restore(snapshot, tmp_path / "restored", actor=OWNER)
    with ContentStore(tmp_path / "restored")._connection() as db:
        assert db.execute("SELECT state FROM sources").fetchone()[0] == "tombstoned"
        assert (
            db.execute("SELECT state FROM parsed_versions").fetchone()[0]
            == "quarantined"
        )
    assert list((tmp_path / "restored/incidents").glob("*.json"))


def test_prepared_run_snapshot_keeps_recovery_evidence(tmp_path):
    from tests.content_adapter_support import material

    bundle, _ = material(tmp_path / "input")
    store = ContentStore.initialize(tmp_path / "store")
    process = launch(store, bundle)
    stop(process)
    run = store.inspect_recovery(actor=OWNER)[0]
    snapshot = tmp_path / "snapshot"
    backup(store, snapshot, actor=OWNER)
    restore(snapshot, tmp_path / "restored", actor=OWNER)
    restored = ContentStore(tmp_path / "restored", read_only=False)
    assert restored.inspect_recovery(actor=OWNER)[0].state == "prepared"
    outcome = restored.recover_run(run.run_id, actor=OWNER)
    assert outcome.outcome == "committed"
    assert (
        restored.read_parsed_payload(outcome.parsed_version_id, actor=OWNER)
        == bundle.normalized_path.read_bytes()
    )


def test_interrupted_restore_root_remains_fenced(tmp_path, monkeypatch):
    store, _, _, _ = seeded(tmp_path)
    snapshot = tmp_path / "snapshot"
    backup(store, snapshot, actor=OWNER)
    import src.content_store.backup as module

    original = module._new_file

    def fail_after_database(artifacts, name, source):
        if name != "content.sqlite3":
            raise OSError(28, "controlled restore failure")
        return original(artifacts, name, source)

    monkeypatch.setattr(module, "_new_file", fail_after_database)
    target = tmp_path / "restore"
    with pytest.raises(ContentStoreError):
        restore(snapshot, target, actor=OWNER)
    assert (target / ".content-recovery-required").exists()
    with pytest.raises(Unavailable):
        ContentStore(target)
