import io

import pytest

from src.content_store.errors import (
    Busy,
    ContentStoreError,
    Unavailable,
)
from src.content_store.models import MAX_BYTES
from src.content_store.store import ContentStore
from tests.content_adapter_support import srt
from tests.content_operations_support import launch, seeded, stop
from tests.content_store_support import OWNER, raw, registration


def test_staging_and_disk_budget_fail_closed(tmp_path, monkeypatch):
    store, bundle, _, first = seeded(tmp_path)
    monkeypatch.setattr("src.content_store.limits.MAX_STAGING_BYTES", 0)
    source = store.register_source(registration("limited"), actor=OWNER)
    with pytest.raises(Unavailable):
        raw(store, source.source_id)
    assert (
        store.read_parsed_payload(first.version.parsed_version_id, actor=OWNER)
        == bundle.normalized_path.read_bytes()
    )
    monkeypatch.setattr("src.content_store.limits.MAX_STAGING_BYTES", 512 * 1024**2)

    def full(*args, **kwargs):
        raise OSError(28, "controlled ENOSPC")

    monkeypatch.setattr("src.content_store.limits.capacity", full)
    another = store.register_source(registration("full"), actor=OWNER)
    with pytest.raises(Unavailable):
        raw(store, another.source_id)
    assert store.read_parsed_payload(first.version.parsed_version_id, actor=OWNER)


def test_active_run_limit_and_explicit_abandonment(tmp_path, monkeypatch):
    store, bundle, _, _ = seeded(tmp_path)
    monkeypatch.setattr("src.content_store.limits.MAX_ACTIVE_RUNS", 0)
    source = store.register_source(registration("active-limit"), actor=OWNER)
    with pytest.raises(Busy):
        raw(store, source.source_id)
    assert store.verify_integrity(actor=OWNER).healthy


def test_oversized_stream_schema_and_lock_are_bounded(tmp_path):
    store, bundle, _, _ = seeded(tmp_path)
    source = store.register_source(registration("oversized"), actor=OWNER)
    with pytest.raises(ContentStoreError):
        store.store_raw_artifact(
            source.source_id,
            io.BytesIO(b"x"),
            expected_sha256="0" * 64,
            expected_size=MAX_BYTES + 1,
            mime_type="text/plain",
            actor=OWNER,
        )
    with store._artifacts.lock(".content-db.lock", exclusive=True):
        with pytest.raises(Busy):
            ContentStore(store.root)
    with store._connection(write=True) as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(Unavailable):
        ContentStore(store.root)


def test_srt_recovery_without_raw_source_reparse(tmp_path, monkeypatch):
    bundle, document = srt(tmp_path / "input")
    store = ContentStore.initialize(tmp_path / "store")
    process = launch(store, bundle)
    stop(process)
    run = store.inspect_recovery(actor=OWNER)[0]

    def forbidden(*args, **kwargs):
        raise AssertionError("no parser")

    monkeypatch.setattr("src.tools_transcribe.import_transcript.import_srt", forbidden)
    monkeypatch.setattr("src.tools_lecture.execute_cs50.validate_document", forbidden)
    bundle.raw_path.unlink()
    result = store.recover_run(run.run_id, actor=OWNER)
    assert result.outcome == "committed"
    assert (
        store.read_parsed_payload(result.parsed_version_id, actor=OWNER)
        == bundle.transcript_path.read_bytes()
    )
    assert [
        b.text
        for b in store.list_content_blocks(result.parsed_version_id, actor=OWNER).items
    ] == [s.text for s in document.segments]


def test_backup_size_limit_is_enforced(tmp_path, monkeypatch):
    from src.content_store.backup import backup

    store, _, _, _ = seeded(tmp_path)
    monkeypatch.setattr("src.content_store.backup.MAX_STORE_BYTES", 1)
    with pytest.raises(Unavailable):
        backup(store, tmp_path / "snapshot", actor=OWNER)
    assert not (tmp_path / "snapshot").exists()


def test_no_recovery_from_caller_intention_or_unknown_run(tmp_path):
    store, _, _, _ = seeded(tmp_path)
    with pytest.raises(ContentStoreError):
        store.recover_run({"verified": True}, actor=OWNER)
    with pytest.raises(ContentStoreError):
        store.recover_run("0" * 32, actor=OWNER)
