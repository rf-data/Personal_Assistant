import pytest

from src.content_store.adapters import import_verified_bundle, verify_material_bundle
from src.content_store.errors import Busy, Forbidden, Unavailable
from src.content_store.models import SourceGrant
from src.content_store.store import ContentStore
from tests.content_adapter_support import material
from tests.content_operations_support import child, launch, line, stop
from tests.content_store_support import OTHER, OWNER, VIEWER


@pytest.mark.parametrize("scope", ["raw", "binding", "parsed"])
@pytest.mark.parametrize("phase", ["prepared", "installed"])
def test_prepared_recovery_real_killed_process(tmp_path, scope, phase, monkeypatch):
    bundle, doc = material(tmp_path / "input")
    store = ContentStore.initialize(tmp_path / "store")
    process = launch(store, bundle, phase, scope)
    with pytest.raises(Busy):
        store.recover_run("0" * 32, actor=OWNER)
    stop(process)
    runs = store.inspect_recovery(actor=OWNER)
    assert len(runs) == 1

    # Recovery must not call adapter gates, parsers, or source files.
    def forbidden(*a, **kw):
        raise AssertionError("no reparse in recovery")

    import src.content_store.publication as publication

    monkeypatch.setattr(publication, "_candidate", forbidden)
    monkeypatch.setattr("src.content_store.adapters._candidate", forbidden)
    outcome = store.recover_run(runs[0].run_id, actor=OWNER)
    assert outcome.outcome == "committed"
    assert store.recover_run(runs[0].run_id, actor=OWNER).outcome == "already_committed"
    if scope == "parsed":
        assert (
            store.read_parsed_payload(outcome.parsed_version_id, actor=OWNER)
            == bundle.normalized_path.read_bytes()
        )
    assert store.verify_integrity(actor=OWNER).healthy


@pytest.mark.parametrize(
    "phase", ["staging", "before_commit", "before_sql_commit", "after_commit"]
)
def test_crash_state_boundaries(tmp_path, phase):
    bundle, doc = material(tmp_path / "input")
    store = ContentStore.initialize(tmp_path / "store")
    process = launch(store, bundle, phase)
    stop(process)
    reopened = ContentStore(store.root, read_only=False)
    if phase == "after_commit":
        assert not reopened.inspect_recovery(actor=OWNER)
        again = import_verified_bundle(
            reopened,
            verify_material_bundle(bundle),
            actor=OWNER,
            request_key="interrupted",
        )
        assert not again.created
        with reopened._connection() as db:
            run_id = db.execute(
                "SELECT id FROM processing_runs WHERE request_key='interrupted'"
            ).fetchone()[0]
        assert reopened.recover_run(run_id, actor=OWNER).outcome == "already_committed"
    else:
        run = reopened.inspect_recovery(actor=OWNER)[0]
        result = reopened.recover_run(run.run_id, actor=OWNER)
        assert result.outcome == ("blocked" if phase == "staging" else "committed")
        if phase == "staging":
            assert (
                reopened.recover_run(run.run_id, actor=OWNER, action="reject").outcome
                == "rejected"
            )
            assert reopened.recover_run(run.run_id, actor=OWNER).outcome == "rejected"


def test_incomplete_prepared_and_acl_change(tmp_path):
    bundle, _ = material(tmp_path / "input")
    store = ContentStore.initialize(tmp_path / "store")
    process = launch(store, bundle)
    stop(process)
    run = store.inspect_recovery(actor=OWNER)[0]
    ref = run.manifest[0]
    (store.root / "staging" / run.run_id / ref.sha256).unlink()
    assert store.recover_run(run.run_id, actor=OWNER).outcome == "blocked"
    assert (
        ContentStore(store.root, read_only=False).inspect_recovery(actor=OWNER)[0].state
        == "blocked"
    )
    with pytest.raises(Forbidden):
        store.recover_run(run.run_id, actor=VIEWER)
    with pytest.raises(Forbidden):
        store.recover_run(run.run_id, actor=OTHER)
    store.set_source_grants(
        run.source_id,
        (SourceGrant(subject="reader"),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    # A different complete prepared run is checked for ACL changes below.


def test_acl_changed_prepared_import_stays_blocked(tmp_path):
    bundle, _ = material(tmp_path / "input")
    store = ContentStore.initialize(tmp_path / "store")
    process = launch(store, bundle)
    stop(process)
    run = store.inspect_recovery(actor=OWNER)[0]
    store.set_source_grants(run.source_id, (), expected_acl_revision=0, actor=OWNER)
    with pytest.raises(Forbidden):
        store.recover_run(run.run_id, actor=OWNER)
    with store._connection() as db:
        assert db.execute("SELECT count(*) FROM parsed_versions").fetchone()[0] == 0


@pytest.mark.parametrize("damage", [None, "header", "frame"])
def test_real_wal_recovery_and_read_only_fence(tmp_path, damage):
    from tests.content_operations_support import seeded

    store, _, _, result = seeded(tmp_path)
    process = child("wal", store.root)
    assert line(process) == dict(phase="wal")
    stop(process)
    wal = store.root / "content.sqlite3-wal"
    assert wal.stat().st_size > 32
    if damage:
        data = bytearray(wal.read_bytes())
        data[0 if damage == "header" else -1] ^= 1
        wal.write_bytes(data)
    original = wal.read_bytes()
    with pytest.raises(Unavailable):
        ContentStore(store.root)
    assert wal.read_bytes() == original
    if damage:
        with pytest.raises(Unavailable):
            ContentStore.recover_database(store.root, actor=OWNER)
        with pytest.raises(Unavailable):
            ContentStore(store.root)
    else:
        report = ContentStore.recover_database(store.root, actor=OWNER)
        assert report.healthy
        assert ContentStore(store.root).read_parsed_payload(
            result.version.parsed_version_id, actor=OWNER
        )
        assert not wal.exists() or wal.stat().st_size == 0


def test_recovery_database_scope_and_live_writer(tmp_path):
    from tests.content_operations_support import seeded

    store, bundle, _, _ = seeded(tmp_path)
    with pytest.raises(Forbidden):
        ContentStore.recover_database(store.root, actor=VIEWER)
    with pytest.raises(Forbidden):
        ContentStore.recover_database(store.root, actor=OTHER)
    # Explicit maintenance is excluded by every active import, independent of age.
    other, _ = material(tmp_path / "second", kind="code")
    process = launch(store, other)
    try:
        with pytest.raises(Busy):
            ContentStore.recover_database(store.root, actor=OWNER)
    finally:
        stop(process)


def test_interrupted_hardlink_install_stays_blocked(tmp_path):
    bundle, _ = material(tmp_path / "input")
    store = ContentStore.initialize(tmp_path / "store")
    process = launch(store, bundle)
    stop(process)
    run = store.inspect_recovery(actor=OWNER)[0]
    ref = run.manifest[0]
    staged = store.root / "staging" / run.run_id / ref.sha256
    installed = store.root / ref.store_key
    installed.parent.mkdir(mode=0o700, exist_ok=True)
    import os

    os.link(staged, installed)
    assert staged.stat().st_nlink == 2
    assert store.recover_run(run.run_id, actor=OWNER).outcome == "blocked"
    assert staged.exists() and installed.exists()
